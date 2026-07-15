"""
PTW/JSA Agent.

Source of truth:
- docs/ShieldEPC_Architecture_Spec_v1.md §3 (Agent Roster), §6 (Zero
  Hallucination Policy)
- PHASE3_PTWJSA_DESIGN.md (approved design checkpoint)

Phase 3 scope: prepares a hazard-aware JSA or PTW draft by combining
two existing, unmodified building blocks:
  1. app.hazards.library.get_hazards() -- deterministic hazard lookup
  2. app.agents.document_generator.DocumentGeneratorAgent -- deterministic
     template rendering

DocumentGeneratorAgent is called as-is and its "answer" string is
returned unmodified in this agent's own "answer" field. Hazard-derived
data (identified_hazards, recommended_controls, required_ppe,
applicable_standards) is returned as separate structured fields --
never appended into the rendered document text. Document composition
that merges the two is deferred to a future template version, per the
approved design decision.

Deterministic composition only -- no generative inference, no clause
interpretation, no free-text fallback. Unknown hazard_ids or an unknown
doc_type raise InsufficientInformation.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ValidationError, field_validator, model_validator

from app.agents.base import Agent, InsufficientInformation
from app.agents.document_generator import DocumentGeneratorAgent
from app.hazards.library import get_hazards

_DOC_TYPE_TO_TEMPLATE_ID = {
    "jsa": "jsa_draft",
    "ptw": "ptw_draft",
}


class PTWJSARequest(BaseModel):
    doc_type: Literal["jsa", "ptw"]
    location: str
    date: str
    performed_by: str
    task_description: str
    selected_hazard_ids: list[str]
    duration: str | None = None

    @field_validator(
        "location", "date", "performed_by", "task_description"
    )
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v

    @field_validator("selected_hazard_ids")
    @classmethod
    def hazard_ids_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("selected_hazard_ids must not be empty")
        return v

    @model_validator(mode="after")
    def duration_required_for_ptw(self) -> "PTWJSARequest":
        if self.doc_type == "ptw" and not (self.duration or "").strip():
            raise ValueError("duration is required when doc_type is 'ptw'")
        return self


def _dedupe_preserve_order(items: tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


class PTWJSAAgent(Agent):
    """
    Combines tenant hazard library lookups with unmodified
    DocumentGeneratorAgent template rendering to produce a
    hazard-aware JSA or PTW draft. See module docstring for the
    approved design boundary (no text is appended to the rendered
    document).
    """

    name = "ptw_jsa_agent"
    version = "0.1.0"

    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        request must contain:
          - doc_type: "jsa" or "ptw"
          - location: str, non-empty
          - date: str, non-empty
          - performed_by: str, non-empty (requester for ptw)
          - task_description: str, non-empty (work description for ptw)
          - selected_hazard_ids: list[str], non-empty, must exist in
            the tenant hazard library
          - duration: str, required only when doc_type == "ptw"

        Raises InsufficientInformation if the request fails validation
        or if any selected_hazard_ids is not present in the tenant
        hazard library -- never fills a gap with a plausible-sounding
        default (spec §6 point 4).
        """
        try:
            validated = PTWJSARequest(**request)
        except ValidationError as exc:
            raise InsufficientInformation(
                f"Invalid PTW/JSA request: {exc}"
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

        identified_hazards = [
            {"hazard_id": h.hazard_id, "hazard_name": h.hazard_name}
            for h in hazards
        ]

        template_id = _DOC_TYPE_TO_TEMPLATE_ID[validated.doc_type]

        if validated.doc_type == "jsa":
            doc_fields = {
                "task_description": validated.task_description,
                "location": validated.location,
                "performed_by": validated.performed_by,
                "date": validated.date,
            }
        else:
            doc_fields = {
                "work_description": validated.task_description,
                "location": validated.location,
                "requested_by": validated.performed_by,
                "date": validated.date,
                "duration": validated.duration,
            }

        doc_result = DocumentGeneratorAgent().run(
            {"template_id": template_id, "fields": doc_fields}
        )

        return {
            "answer": doc_result["answer"],
            "confidence_score": 1.0,
            "confidence_basis": (
                "Deterministic composition: hazard_ids were resolved "
                "against the tenant hazard library and the document "
                "was rendered by DocumentGeneratorAgent from caller-"
                "supplied fields, with no generative inference or "
                "clause interpretation performed."
            ),
            "source_of_reasoning": [
                {
                    "type": "structured_input",
                    "ref": f"caller_supplied_fields:{template_id}",
                },
                {
                    "type": "structured_input",
                    "ref": "tenant_hazard_library:selected_hazards",
                },
            ],
            "missing_information": [],
            "assumptions_made": [],
            "applicable_standards": applicable_standards,
            "identified_hazards": identified_hazards,
            "recommended_controls": recommended_controls,
            "required_ppe": required_ppe,
            "human_review_required": True,
            "human_review_reason": "statutory_requirement",
        }
