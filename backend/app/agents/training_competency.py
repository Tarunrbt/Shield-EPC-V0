"""
Training & Competency Agent.

Source of truth:
- docs/ShieldEPC_Architecture_Spec_v1.md §3 (Agent Roster), §6 (Zero
  Hallucination Policy)
- backend/docs/PHASE4B_TRAINING_COMPETENCY_DESIGN.md (approved design
  checkpoint)

Phase 4B scope (first cut): deterministic comparison of caller-supplied
training records against a caller-supplied list of required
competencies for a role/task. No LMS integration, no qualitative
judgment of training adequacy, no auto-scheduling -- deferred per the
design doc's explicit non-goals.

Deterministic validation/composition only -- no LLM call, no generative
inference. The agent never infers what competencies a role requires;
that list must be supplied by the caller.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ValidationError, field_validator

from app.agents.base import Agent, InsufficientInformation


class TrainingRecord(BaseModel):
    competency_name: str
    completed: bool
    completion_date: str | None = None
    expiry_date: str | None = None
    issuing_body: str | None = None

    @field_validator("competency_name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v


class TrainingCompetencyRequest(BaseModel):
    role_or_task: str
    assessment_date: str
    required_competencies: list[str]
    training_records: list[TrainingRecord]

    @field_validator("role_or_task", "assessment_date")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v

    @field_validator("required_competencies")
    @classmethod
    def required_competencies_non_empty_entries(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("required_competencies must have at least one entry")
        if any(not entry.strip() for entry in v):
            raise ValueError("required_competencies entries must not be blank")
        return v


class TrainingCompetencyAgent(Agent):
    """
    Validates caller-supplied training records against caller-supplied
    required competencies. See module docstring for the approved design
    boundary (no qualitative judgment, no inferred requirements,
    mandatory human review).
    """

    name = "training_competency_agent"
    version = "0.1.0"

    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        request must contain:
          - role_or_task: str, non-empty
          - assessment_date: str (ISO8601), non-empty
          - required_competencies: list[str], non-empty, no blank entries
          - training_records: list[TrainingRecord] (may be empty)

        Raises InsufficientInformation if the request fails validation
        or contains an unparseable date -- never fills a gap with a
        plausible-sounding default (spec §6 point 4).
        """
        try:
            validated = TrainingCompetencyRequest(**request)
        except ValidationError as exc:
            raise InsufficientInformation(
                f"Invalid training competency request: {exc}"
            )

        try:
            assessment_date = date.fromisoformat(validated.assessment_date)
        except ValueError:
            raise InsufficientInformation(
                f"assessment_date '{validated.assessment_date}' is not a "
                "valid ISO8601 date"
            )

        records_by_name: dict[str, TrainingRecord] = {}
        for record in validated.training_records:
            try:
                if record.expiry_date is not None:
                    date.fromisoformat(record.expiry_date)
                if record.completion_date is not None:
                    date.fromisoformat(record.completion_date)
            except ValueError:
                raise InsufficientInformation(
                    f"training record for '{record.competency_name}' has "
                    "an unparseable date"
                )
            records_by_name[record.competency_name] = record

        missing_information: list[str] = []
        satisfied: list[str] = []

        for competency in validated.required_competencies:
            record = records_by_name.get(competency)

            if record is None:
                missing_information.append(f"missing: {competency}")
                continue

            if not record.completed:
                missing_information.append(f"missing: {competency} (not completed)")
                continue

            if record.expiry_date is not None:
                expiry = date.fromisoformat(record.expiry_date)
                if expiry < assessment_date:
                    missing_information.append(
                        f"expired: {competency} (expired {record.expiry_date})"
                    )
                    continue

            satisfied.append(competency)

        has_gap = len(missing_information) > 0

        answer = (
            "DRAFT — PENDING HUMAN REVIEW\n"
            f"Role/task: {validated.role_or_task}\n"
            f"Assessment date: {validated.assessment_date}\n"
            f"Satisfied: {len(satisfied)}/{len(validated.required_competencies)}\n"
            f"Gaps: {len(missing_information)}\n"
        )

        return {
            "answer": answer,
            "confidence_score": 1.0,
            "confidence_basis": (
                "Deterministic comparison: caller-supplied training "
                "records were checked against caller-supplied required "
                "competencies for presence, completion, and expiry, "
                "with no generative inference performed."
            ),
            "source_of_reasoning": [
                {
                    "type": "structured_input",
                    "ref": "caller_supplied_training_records:training_competency",
                }
            ],
            "missing_information": missing_information,
            "assumptions_made": [],
            "applicable_standards": [],
            "human_review_required": True,
            "human_review_reason": (
                "compliance_gap_flagged" if has_gap else "statutory_requirement"
            ),
        }
