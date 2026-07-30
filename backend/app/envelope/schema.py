"""
Mandatory response envelope schema.

Source of truth: docs/ShieldEPC_Architecture_Spec_v1.md §5.
Every AI-generated response, regardless of which agent produced it, is
wrapped in this shape before it reaches a client. Do not add, rename, or
drop fields here without updating §5 first — this file must always match
that section exactly (README.md: "Code that doesn't match this document
is a bug in the code or a stale document").
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

class SourceType(str, Enum):
    STANDARD_CLAUSE = "standard_clause"
    TENANT_DOCUMENT = "tenant_document"
    STRUCTURED_INPUT = "structured_input"

class SourceOfReasoning(BaseModel):
    """One grounding citation. §6 point 1: no claim without a retrieved source."""

    type: SourceType
    ref: str
    retrieved_date: Optional[str] = None
    excerpt_ref: Optional[str] = None

class InvestigatorSignoff(BaseModel):
    investigator_id: str | None = None
    status: Literal["pending", "signed", "rejected"] = "pending"
    signed_at: datetime | None = Field(
        default=None,
        description="ISO 8601 timezone-aware timestamp",
    )

    @model_validator(mode="after")
    def check_signed_at_consistency(self):
        if self.status == "pending" and self.signed_at is not None:
            raise ValueError(
                "signed_at must be None while status is 'pending'"
            )

        if (
            self.status in {"signed", "rejected"}
            and self.investigator_id is None
        ):
            raise ValueError(
                "investigator_id is required when status is 'signed' or 'rejected'"
            )

        if self.signed_at is not None and (
            self.signed_at.tzinfo is None
            or self.signed_at.utcoffset() is None
        ):
            raise ValueError(
                "signed_at must be timezone-aware"
            )

        return self


class EnvelopeContent(BaseModel):
    answer: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_basis: str

    five_whys: list[str] | None = None
    fishbone_causes: dict | None = None
    bowtie: dict | None = None
    investigator_signoff: InvestigatorSignoff | None = None


HumanReviewReason = Literal[
    "risk_rating_high",
    "compliance_gap_flagged",
    "low_confidence",
    "statutory_requirement",
]


class ResponseEnvelope(BaseModel):
    response_id: str
    tenant_id: str
    agent: str
    agent_version: str
    model_version: str
    timestamp: str  # ISO8601

    content: EnvelopeContent

    source_of_reasoning: list[SourceOfReasoning] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    assumptions_made: list[str] = Field(default_factory=list)
    applicable_standards: list[str] = Field(default_factory=list)

    human_review_required: bool
    human_review_reason: Optional[HumanReviewReason] = None

    audit_trail_id: str
    schema_version: Literal["1.0"] = "1.0"

    model_config = ConfigDict(
    use_enum_values=True,
)

    def model_post_init(self, __context: Any) -> None:
        if self.human_review_required and self.human_review_reason is None:
            raise ValueError(
                "human_review_required=True requires human_review_reason to be set"
            )
