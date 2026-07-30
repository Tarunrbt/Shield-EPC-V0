"""
Tests for Orchestrator routing and audit/envelope guarantees.

Covers the two failure paths that must never bypass the audit log or
skip envelope assembly:
  1. Unknown operation_type (KeyError in routing table)
  2. Unexpected agent/verifier exceptions (non-InsufficientInformation)
"""

from unittest.mock import MagicMock

import pytest

from app.agents.base import InsufficientInformation
from app.orchestrator import Orchestrator


def _make_orchestrator():
    audit_log = MagicMock()
    audit_log.append.return_value = MagicMock(entry_id="audit-entry-123")

    envelope_assembler = MagicMock()
    envelope_assembler.assemble.side_effect = lambda **kwargs: kwargs

    verifier = MagicMock()

    document_generator_agent = MagicMock()
    document_generator_agent.name = "document_generator"
    document_generator_agent.version = "1.0"

    risk_assessment_agent = MagicMock()
    risk_assessment_agent.name = "risk_assessment"
    risk_assessment_agent.version = "1.0"

    ptw_jsa_agent = MagicMock()
    ptw_jsa_agent.name = "ptw_jsa"
    ptw_jsa_agent.version = "1.0"

    incident_investigation_agent = MagicMock()
    incident_investigation_agent.name = "incident_investigation"
    incident_investigation_agent.version = "1.0"

    training_competency_agent = MagicMock()
    training_competency_agent.name = "training_competency"
    training_competency_agent.version = "1.0"

    orchestrator = Orchestrator(
        audit_log=audit_log,
        envelope_assembler=envelope_assembler,
        verifier=verifier,
        document_generator_agent=document_generator_agent,
        risk_assessment_agent=risk_assessment_agent,
        ptw_jsa_agent=ptw_jsa_agent,
        incident_investigation_agent=incident_investigation_agent,
        training_competency_agent=training_competency_agent,
    )
    return orchestrator, audit_log, envelope_assembler, document_generator_agent


def test_unknown_operation_type_returns_envelope_not_exception():
    """
    Previously: unknown operation_type raised a raw InsufficientInformation
    that bypassed both the audit log and envelope assembly. This must now
    return a valid, human-review-flagged envelope and log the attempt.
    """
    orchestrator, audit_log, envelope_assembler, _ = _make_orchestrator()

    result = orchestrator.handle(
        operation_type="nonexistent_type",
        request={},
        tenant_id="test-tenant",
    )

    # No exception should propagate -- envelope_assembler.assemble was called.
    envelope_assembler.assemble.assert_called_once()
    call_kwargs = envelope_assembler.assemble.call_args.kwargs

    assert call_kwargs["human_review_required"] is True
    assert call_kwargs["human_review_reason"] == "low_confidence"
    assert call_kwargs["confidence_score"] == 0.0
    assert "Unknown operation_type" in call_kwargs["missing_information"][0]
    assert call_kwargs["audit_trail_id"] == "audit-entry-123"

    # Audit log must record the attempt even though the type was unknown.
    audit_log.append.assert_called_once()
    audit_payload = audit_log.append.call_args.kwargs["payload"]
    assert audit_payload["outcome"] == "insufficient_information"
    assert "Unknown operation_type" in audit_payload["reason"]


def test_agent_exception_is_logged_then_reraised():
    """
    Previously: a non-InsufficientInformation exception from agent.run()
    or verifier.run() propagated with zero audit trail. This must now be
    logged as an "error" outcome before re-raising.
    """
    orchestrator, audit_log, envelope_assembler, document_generator_agent = (
        _make_orchestrator()
    )
    document_generator_agent.run.side_effect = RuntimeError("boom: upstream API down")

    with pytest.raises(RuntimeError, match="boom: upstream API down"):
        orchestrator.handle(
            operation_type="document_generation",
            request={"foo": "bar"},
            tenant_id="test-tenant",
        )

    audit_log.append.assert_called_once()
    audit_payload = audit_log.append.call_args.kwargs["payload"]
    assert audit_payload["outcome"] == "error"
    assert audit_payload["error_type"] == "RuntimeError"
    assert "boom: upstream API down" in audit_payload["reason"]

    # Envelope must NOT have been assembled for a genuine system failure.
    envelope_assembler.assemble.assert_not_called()
