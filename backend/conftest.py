from pathlib import Path

import pytest


def _post_generate(client):
    """
    Standalone helper mirroring test_api.py's /generate payload.
    Not calling test_api.test_generate() directly -- that is a pytest
    test function, not a reusable helper, and running it twice would
    duplicate the request's side effects (a fresh audit log entry).
    """
    payload = {
        "template_id": "jsa_draft",
        "fields": {
            "task_description": "Excavation near buried services",
            "location": "Zone 4",
            "performed_by": "Test User",
            "date": "2026-07-14",
        },
        "tenant_id": "tenant_test_001",
        "user_id": "user_test_001",
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def envelope():
    """
    Reuses test_api.py's already-configured client and audit_log
    (same app instance, same AUDIT_LOG_PATH) so audit_trail_id in the
    returned envelope matches what audit_log.read_all() sees.
    The audit log is truncated first (via its private _path attribute)
    so exactly one entry exists when test_audit_log_entry runs.
    """
    from test_api import client, audit_log

    Path(audit_log._path).write_text("")

    return _post_generate(client)


@pytest.fixture
def tenant_id():
    return "tenant_test_001"


@pytest.fixture
def user_id():
    return "user_test_001"


@pytest.fixture
def orchestrator(tmp_path):
    from app.agents.document_generator import DocumentGeneratorAgent
    from app.agents.risk_assessment import RiskAssessmentAgent
    from app.agents.ptw_jsa import PTWJSAAgent
    from app.agents.verifier import VerifierAgent
    from app.audit.log import AuditLog
    from app.envelope.middleware import EnvelopeAssembler
    from app.orchestrator import Orchestrator

    audit_log = AuditLog(tmp_path / "audit_log.jsonl")
    envelope_assembler = EnvelopeAssembler(model_version="phase1-e2e-test")

    return Orchestrator(
        audit_log=audit_log,
        envelope_assembler=envelope_assembler,
        verifier=VerifierAgent(),
        document_generator_agent=DocumentGeneratorAgent(),
        risk_assessment_agent=RiskAssessmentAgent(),
        ptw_jsa_agent=PTWJSAAgent(),
    )
