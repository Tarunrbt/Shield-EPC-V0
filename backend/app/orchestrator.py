"""
Orchestrator Agent -- routing skeleton.

Source of truth: docs/ShieldEPC_Architecture_Spec_v1.md §2 (High-Level
Architecture) and §4 (Orchestrator Agent Design).

Phase 1 scope (ROADMAP.md): prove envelope assembly, audit logging, and
the human-review gate work end-to-end with one agent, before any domain
routing complexity is added. This is deliberately NOT an intent
classifier yet -- it accepts an already-selected Agent instance and
wires it to the audit log and envelope assembler correctly. Real
intent-based routing is added once more than one agent exists.
"""

from __future__ import annotations

from app.agents.base import Agent, InsufficientInformation
from app.audit.log import AuditEventType, AuditLog
from app.envelope.middleware import EnvelopeAssembler
from app.envelope.schema import ResponseEnvelope
from app.agents.verifier import VerifierAgent

import logging

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Wires one agent call to the audit log and envelope assembler.

    Ordering matters and is not incidental: the audit entry for the
    agent's raw result is appended FIRST, and its entry_id is then
    passed into EnvelopeAssembler as audit_trail_id. This is the only
    order that lets audit_trail_id in the envelope actually point to a
    real, hash-chained log entry rather than a fabricated reference --
    per the spec's own instruction that audit_trail_id "links to an
    immutable audit log entry."
    """

    def __init__(
        self,
        audit_log: AuditLog,
        envelope_assembler: EnvelopeAssembler,
        verifier: VerifierAgent,
        document_generator_agent: Agent,
        risk_assessment_agent: Agent,
        ptw_jsa_agent: Agent,
    ) -> None:
        self.audit_log = audit_log
        self.envelope_assembler = envelope_assembler
        self.verifier = verifier
        self._routing = {
            "document_generation": document_generator_agent,
            "risk_assessment": risk_assessment_agent,
            "ptw_jsa": ptw_jsa_agent,
        }

    def handle(
        self,
        *,
        operation_type: str,
        request: dict,
        tenant_id: str,
        user_id: str | None = None,
    ) -> ResponseEnvelope:
        """
        Routes a request to the appropriate domain agent based on operation_type,
        logs the outcome (success or InsufficientInformation) to the audit trail,
        then assembles and returns the envelope.

        operation_type selects which agent will process the request:
        - "document_generation" → DocumentGeneratorAgent
        - "risk_assessment" → RiskAssessmentAgent
        - "ptw_jsa" → PTWJSAAgent

        Verification and envelope assembly happen after agent selection.
        """
        # Select agent from routing table
        try:
            agent = self._routing[operation_type]
        except KeyError:
            exc = InsufficientInformation(
                f"Unknown operation_type: {operation_type}"
            )
            audit_entry = self.audit_log.append(
                event_type=AuditEventType.AGENT_INVOCATION,
                tenant_id=tenant_id,
                user_id=user_id,
                payload={
                    "agent": None,
                    "agent_version": None,
                    "request": request,
                    "outcome": "insufficient_information",
                    "reason": str(exc),
                },
            )
            return self.envelope_assembler.assemble(
                tenant_id=tenant_id,
                agent_name="orchestrator",
                agent_version="n/a",
                answer="",
                confidence_score=0.0,
                confidence_basis="insufficient_information: no fabricated answer produced",
                source_of_reasoning=[],
                missing_information=[str(exc)],
                human_review_required=True,
                human_review_reason="low_confidence",
                audit_trail_id=audit_entry.entry_id,
            )

        try:
            result = agent.run(request)
            # Phase 2 verification pass.
            verified_result = self.verifier.run(result)
        except InsufficientInformation as exc:
            # No dedicated "insufficient information" event type exists in
            # AuditEventType (only AGENT_INVOCATION, HUMAN_REVIEW_ACTION,
            # DOCUMENT_VERSION as of audit/log.py line 34-37), so this is
            # logged as AGENT_INVOCATION with the outcome captured in the
            # payload itself, not inferred from event_type.
            audit_entry = self.audit_log.append(
                event_type=AuditEventType.AGENT_INVOCATION,
                tenant_id=tenant_id,
                user_id=user_id,
                payload={
                    "agent": agent.name,
                    "agent_version": agent.version,
                    "request": request,
                    "outcome": "insufficient_information",
                    "reason": str(exc),
                },
            )
            return self.envelope_assembler.assemble(
                tenant_id=tenant_id,
                agent_name=agent.name,
                agent_version=agent.version,
                answer="",
                confidence_score=0.0,
                confidence_basis="insufficient_information: no fabricated answer produced",
                source_of_reasoning=[],
                missing_information=[str(exc)],
                human_review_required=True,
                human_review_reason="low_confidence",
                audit_trail_id=audit_entry.entry_id,
            )
        except Exception as exc:
            # System/agent-execution failures (API errors, timeouts, bugs)
            # are NOT InsufficientInformation: they mean the pipeline itself
            # broke, not that the agent lacked grounding data. The audit
            # log's hash-chained, immutable design requires every invocation
            # attempt -- including failed ones -- to leave a record. Letting
            # this propagate unlogged meant a crash left zero audit trail of
            # the attempt ever happening.
            self.audit_log.append(
                event_type=AuditEventType.AGENT_INVOCATION,
                tenant_id=tenant_id,
                user_id=user_id,
                payload={
                    "agent": agent.name,
                    "agent_version": agent.version,
                    "request": request,
                    "outcome": "error",
                    "error_type": type(exc).__name__,
                    "reason": str(exc),
                },
            )
            logger.exception(
                "agent execution failed: agent=%s operation_type=%s",
                agent.name,
                operation_type,
            )
            raise

        verification_meta = {
            "verification_status": verified_result.pop("verification_status", None),
            "verification_agent": verified_result.pop("verification_agent", None),
            "verification_agent_version": verified_result.pop("verification_agent_version", None),
        }

        audit_entry = self.audit_log.append(
            event_type=AuditEventType.AGENT_INVOCATION,
            tenant_id=tenant_id,
            user_id=user_id,
            payload={
                "agent": agent.name,
                "agent_version": agent.version,
                "result": result,
                "outcome": "success",
                "verification": verification_meta,
            },
        )

        _ENVELOPE_ALLOWED_KEYS = {
            "answer",
            "confidence_score",
            "confidence_basis",
            "source_of_reasoning",
            "missing_information",
            "assumptions_made",
            "applicable_standards",
            "human_review_required",
            "human_review_reason",
        }

        envelope_payload = {
            k: v for k, v in verified_result.items() if k in _ENVELOPE_ALLOWED_KEYS
        }
        dropped = set(verified_result.keys()) - _ENVELOPE_ALLOWED_KEYS
        if dropped:
            logger.info(
                "envelope filter: agent=%s dropped domain-specific keys "
                "from envelope (retained in audit log payload only): %s",
                agent.name,
                sorted(dropped),
            )

        return self.envelope_assembler.assemble(
            tenant_id=tenant_id,
            agent_name=agent.name,
            agent_version=agent.version,
            audit_trail_id=audit_entry.entry_id,
            **envelope_payload,
        )
