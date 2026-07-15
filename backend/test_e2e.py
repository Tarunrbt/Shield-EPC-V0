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


if __name__ == "__main__":
    main()
