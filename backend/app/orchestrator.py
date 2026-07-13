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

    def __init__(self, audit_log: AuditLog, envelope_assembler: EnvelopeAssembler) -> None:
        self.audit_log = audit_log
        self.envelope_assembler = envelope_assembler

    def handle(
        self,
        *,
        agent: Agent,
        request: dict,
        tenant_id: str,
        user_id: str | None = None,
    ) -> ResponseEnvelope:
        """
        Runs one agent against a request, logs the outcome (success or
        InsufficientInformation) to the audit trail, then assembles and
        returns the envelope. Does not run the Verifier Agent pass --
        that is a separate Phase 1 component, called before this method
        once it exists (spec §6 point 2: verification happens before
        envelope assembly).
        """
        try:
            result = agent.run(request)
            # Phase 1 verification pass.
            verified_result = result
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

        audit_entry = self.audit_log.append(
            event_type=AuditEventType.AGENT_INVOCATION,
            tenant_id=tenant_id,
            user_id=user_id,
            payload={
                "agent": agent.name,
                "agent_version": agent.version,
                "result": result,
                "outcome": "success",
            },
        )

        return self.envelope_assembler.assemble(
            tenant_id=tenant_id,
            agent_name=agent.name,
            agent_version=agent.version,
            audit_trail_id=audit_entry.entry_id,
            **verified_result,
        )


