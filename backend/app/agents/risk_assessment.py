"""
Risk Assessment Agent.

Source of truth:
- docs/ShieldEPC_Architecture_Spec_v1.md §3 (Agent Roster), §6 (Zero
  Hallucination Policy)
- Phase 3 Step 1 locked design (Tenant Hazard Library)

Phase 3 scope: aggregates controls, PPE, and applicable standards for a
caller-supplied set of hazard_ids drawn exclusively from the tenant
hazard library (app.hazards.library). Computes only the raw product
risk_score = likelihood * severity. This is NOT the tenant-configurable
risk matrix -- risk_level remains None until that later phase exists.

Deterministic lookup only -- no generative inference, no clause
interpretation, no free-text fallback. Unknown hazard_ids raise
InsufficientInformation via get_hazards(), per base.py's contract.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError, field_validator

from app.agents.base import Agent, InsufficientInformation
from app.hazards.library import get_hazards


class RiskAssessmentRequest(BaseModel):
    task_description: str
    selected_hazard_ids: list[str]
    likelihood: int
    severity: int

    @field_validator("task_description")
    @classmethod
    def task_description_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("task_description must not be empty")
        return v

    @field_validator("selected_hazard_ids")
    @classmethod
    def hazard_ids_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("selected_hazard_ids must not be empty")
        return v

    @field_validator("likelihood", "severity")
    @classmethod
    def score_in_range(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("must be between 1 and 5 inclusive")
        return v


def _dedupe_preserve_order(items: tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


class RiskAssessmentAgent(Agent):
    """
    Aggregates controls, PPE, and applicable standards for a set of
    tenant-hazard-library hazard_ids. See module docstring for what is
    and is not yet computed (risk_level is deferred to a later phase).
    """

    name = "risk_assessment_agent"
    version = "0.1.0"

    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        request must contain:
          - task_description: str, non-empty
          - selected_hazard_ids: list[str], non-empty, must exist in
            the tenant hazard library
          - likelihood: int, 1-5
          - severity: int, 1-5

        Raises InsufficientInformation if the request fails validation
        or if any selected_hazard_ids is not present in the tenant
        hazard library -- never fills a gap with a plausible-sounding
        default (spec §6 point 4).
        """
        try:
            validated = RiskAssessmentRequest(**request)
        except ValidationError as exc:
            raise InsufficientInformation(
                f"Invalid risk assessment request: {exc}"
            )

        hazards = get_hazards(tuple(validated.selected_hazard_ids))

        recommended_controls: list[str] = []
        required_ppe: list[str] = []
        applicable_standards: list[str] = []
        for hazard in hazards:
            recommended_controls.extend(hazard.default_controls)
            required_ppe.extend(hazard.required_ppe)
            applicable_standards.extend(hazard.applicable_standards)

        recommended_controls = _dedupe_preserve_order(tuple(recommended_controls))
        required_ppe = _dedupe_preserve_order(tuple(required_ppe))
        applicable_standards = _dedupe_preserve_order(tuple(applicable_standards))

        risk_score = validated.likelihood * validated.severity

        identified_hazards = [
            {"hazard_id": h.hazard_id, "hazard_name": h.hazard_name}
            for h in hazards
        ]

        answer = (
            f"Risk assessment for: {validated.task_description}\n"
            f"Identified hazards: "
            f"{', '.join(h.hazard_name for h in hazards)}\n"
            f"Likelihood: {validated.likelihood}, Severity: "
            f"{validated.severity}, Raw risk score: {risk_score}\n"
            f"Risk classification: pending tenant-configurable risk "
            f"matrix (not yet implemented)."
        )

        return {
            "answer": answer,
            "confidence_score": 1.0,
            "confidence_basis": (
                "Deterministic lookup: all hazard_ids were present in "
                "the tenant hazard library and controls/PPE/standards "
                "were aggregated directly, with no generative inference "
                "or clause interpretation performed."
            ),
            "source_of_reasoning": [
                {
                    "type": "structured_input",
                    "ref": "tenant_hazard_library:selected_hazards",
                }
            ],
            "missing_information": [],
            "assumptions_made": [],
            "applicable_standards": applicable_standards,
            "identified_hazards": identified_hazards,
            "recommended_controls": recommended_controls,
            "required_ppe": required_ppe,
            "risk_score": risk_score,
            "risk_level": None,
            "human_review_required": True,
            "human_review_reason": "statutory_requirement",
        }
