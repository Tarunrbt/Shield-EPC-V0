"""
Phase 1 end-to-end wiring test.

Run from backend/ with:
    python3 test_e2e.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from app.agents.document_generator import DocumentGeneratorAgent
from app.agents.risk_assessment import RiskAssessmentAgent
from app.agents.ptw_jsa import PTWJSAAgent
from app.audit.log import AuditLog
from app.envelope.middleware import EnvelopeAssembler
from app.envelope.schema import ResponseEnvelope
from app.orchestrator import Orchestrator
from app.agents.verifier import VerifierAgent


def check(condition: bool, message: str) -> None:
    if not condition:
        print(f"FAIL: {message}")
        sys.exit(1)
    print(f"OK:   {message}")


def main() -> None:
    temp_dir = Path(tempfile.mkdtemp(prefix="shield_epc_e2e_"))
    audit_log_path = temp_dir / "audit_log.jsonl"

    audit_log = AuditLog(audit_log_path)
    envelope_assembler = EnvelopeAssembler(
        model_version="phase1-e2e-test"
    )

    orchestrator = Orchestrator(
        audit_log=audit_log,
        envelope_assembler=envelope_assembler,
        verifier=VerifierAgent(),
        document_generator_agent=DocumentGeneratorAgent(),
        risk_assessment_agent=RiskAssessmentAgent(),
        ptw_jsa_agent=PTWJSAAgent(),
    )

    agent = DocumentGeneratorAgent()

    tenant_id = "tenant_test_001"
    user_id = "user_test_001"

    request = {
        "template_id": "jsa_draft",
        "fields": {
            "task_description": "Excavation near buried services",
            "location": "Zone 4",
            "performed_by": "Test User",
            "date": "2026-07-13",
        },
    }

    envelope = orchestrator.handle(
        operation_type="document_generation",
        request=request,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    check(
        isinstance(envelope, ResponseEnvelope),
        "handle() returns ResponseEnvelope",
    )

    check(
        envelope.tenant_id == tenant_id,
        "tenant_id preserved",
    )

    check(
        envelope.agent == agent.name,
        "agent name preserved",
    )

    check(
        envelope.agent_version == agent.version,
        "agent version preserved",
    )

    test_risk_assessment_and_ptw_jsa_envelope_compatibility(
        orchestrator, tenant_id, user_id
    )


    check(
        bool(envelope.audit_trail_id),
        "audit_trail_id generated",
    )

    entries = audit_log.read_all()

    check(
        len(entries) == 1,
        "one audit entry created",
    )

    check(
        entries[0]["entry_id"] == envelope.audit_trail_id,
        "audit_trail_id matches audit entry",
    )

    check(
        entries[0]["payload"]["outcome"] == "success",
        "audit outcome is success",
    )

    print("\n✅ Phase 1 end-to-end wiring test PASSED")


def test_risk_assessment_and_ptw_jsa_envelope_compatibility(orchestrator, tenant_id, user_id):
    """
    Phase 4.2.1 regression test.

    Confirms the envelope filter patch: RiskAssessmentAgent and PTWJSAAgent
    both produce domain-specific keys (risk_score, identified_hazards, etc.)
    that are NOT in EnvelopeAssembler.assemble()'s signature. Before the
    Phase 4.2.1 patch, this call would raise TypeError. This test exists
    because test_e2e.py's original coverage only exercised
    operation_type="document_generation", never these two.
    """
    risk_envelope = orchestrator.handle(
        operation_type="risk_assessment",
        request={
            "task_description": "Excavation near buried services",
            "selected_hazard_ids": ["excavation"],
            "likelihood": 2,
            "severity": 3,
        },
        tenant_id=tenant_id,
        user_id=user_id,
    )
    check(
        isinstance(risk_envelope, ResponseEnvelope),
        "risk_assessment: handle() returns ResponseEnvelope without TypeError",
    )
    check(
        risk_envelope.content.confidence_score == 1.0,
        "risk_assessment: envelope confidence_score preserved",
    )

    jsa_envelope = orchestrator.handle(
        operation_type="ptw_jsa",
        request={
            "doc_type": "jsa",
            "location": "Zone 4",
            "date": "2026-07-15",
            "performed_by": "Test User",
            "task_description": "Excavation near buried services",
            "selected_hazard_ids": ["excavation", "confined_space"],
        },
        tenant_id=tenant_id,
        user_id=user_id,
    )
    check(
        isinstance(jsa_envelope, ResponseEnvelope),
        "ptw_jsa: handle() returns ResponseEnvelope without TypeError",
    )
    check(
        "JOB SAFETY ANALYSIS" in jsa_envelope.content.answer,
        "ptw_jsa: envelope answer contains rendered JSA content",
    )


if __name__ == "__main__":
    main()
