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
from app.agents.incident_investigation import IncidentInvestigationAgent


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
        incident_investigation_agent=IncidentInvestigationAgent(),
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


    test_risk_assessment_and_ptw_jsa_envelope_compatibility(
        orchestrator, tenant_id, user_id
    )

    test_incident_investigation_envelope_compatibility(
        orchestrator, tenant_id, user_id
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


def test_incident_investigation_envelope_compatibility(
    orchestrator,
    tenant_id,
    user_id,
):
    incident_envelope = orchestrator.handle(
        operation_type="incident_investigation",
        request={
            "incident_description": "Worker slipped on wet floor",
            "five_whys": [
                "Worker slipped",
                "Floor was wet",
                "Leak was not repaired",
            ],
            "fishbone_causes": {
                "people_factors": ["Inadequate hazard awareness"],
                "process": ["No inspection routine"],
                "equipment": [],
                "materials": [],
                "environment": ["Wet floor"],
            },
            "bowtie_top_event": "Slip and fall",
            "bowtie_threats": ["Wet surface"],
            "bowtie_consequences": ["Minor injury"],
            "preventive_barriers": ["Routine inspections"],
            "mitigative_barriers": ["First aid"],
        },
        tenant_id=tenant_id,
        user_id=user_id,
    )

    check(
        isinstance(incident_envelope, ResponseEnvelope),
        "incident_investigation: handle() returns ResponseEnvelope",
    )

    check(
        incident_envelope.human_review_required is True,
        "incident_investigation: human review required",
    )

    check(
        incident_envelope.human_review_reason == "statutory_requirement",
        "incident_investigation: review reason preserved",
    )

    check(
        incident_envelope.content.investigator_signoff.status == "pending",
        "incident_investigation: investigator sign-off remains unset",
    )

    check(
        incident_envelope.content.five_whys[0] == "Worker slipped",
        "incident_investigation: five_whys preserved",
    )

    check(
        incident_envelope.content.fishbone_causes["people_factors"]
        == ["Inadequate hazard awareness"],
        "incident_investigation: fishbone preserved",
    )

    check(
        incident_envelope.content.bowtie["top_event"] == "Slip and fall",
        "incident_investigation: bowtie preserved",
    )

    check(
        bool(incident_envelope.audit_trail_id),
        "incident_investigation: audit_trail_id generated",
    )


if __name__ == "__main__":
    main()
