"""
Envelope assembly for Shield EPC.

Source of truth: docs/ShieldEPC_Architecture_Spec_v1.md §5 (Mandatory
Output Envelope) and §6 (Zero Hallucination Policy).

This module builds the response envelope one layer above individual
agents, per base.py's Agent.run() contract: agents return a raw result
dict, never an envelope. Assembly is the Orchestrator's job.

Validation (bounds on confidence_score, the human_review_reason enum,
the human_review_required/reason pairing) all lives in schema.py's
ResponseEnvelope model, not here. This module's only job is to build
one from agent output -- it must not re-implement or shadow that
validation, per schema.py's own instruction not to let this drift.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.envelope.schema import (
    EnvelopeContent,
    HumanReviewReason,
    ResponseEnvelope,
    SourceOfReasoning,
)


class EnvelopeAssembler:
    """
    Wraps a raw agent result into a validated ResponseEnvelope (spec §5).
    Does not perform verification itself -- the Verifier Agent's pass
    (§6 point 2) must happen before this is called, so that
    source_of_reasoning is already checked against content.answer by
    the time assembly occurs.
    """

    def __init__(self, model_version: str) -> None:
        # model_version is injected (e.g. "claude-sonnet-4-6-2026xxxx")
        # rather than hardcoded, since it will change across deployments.
        self.model_version = model_version

    def assemble(
        self,
        *,
        tenant_id: str,
        agent_name: str,
        agent_version: str,
        answer: str,
        confidence_score: float,
        confidence_basis: str,
        source_of_reasoning: list[SourceOfReasoning],
        missing_information: list[str] | None = None,
        assumptions_made: list[str] | None = None,
        applicable_standards: list[str] | None = None,
        human_review_required: bool,
        human_review_reason: HumanReviewReason | None = None,
        audit_trail_id: str,
    ) -> ResponseEnvelope:
        """
        Builds one ResponseEnvelope per the §5 contract. All fields are
        explicit keyword-only args -- no field is silently defaulted to
        a fabricated value. Pydantic (schema.py) enforces confidence_score
        bounds, the human_review_reason enum, and the
        human_review_required/reason pairing; this method does not
        duplicate those checks.
        """
        return ResponseEnvelope(
            response_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            agent=agent_name,
            agent_version=agent_version,
            model_version=self.model_version,
            timestamp=datetime.now(timezone.utc).isoformat(),
            content=EnvelopeContent(
                answer=answer,
                confidence_score=confidence_score,
                confidence_basis=confidence_basis,
            ),
            source_of_reasoning=source_of_reasoning,
            missing_information=missing_information or [],
            assumptions_made=assumptions_made or [],
            applicable_standards=applicable_standards or [],
            human_review_required=human_review_required,
            human_review_reason=human_review_reason,
            audit_trail_id=audit_trail_id,
        )

