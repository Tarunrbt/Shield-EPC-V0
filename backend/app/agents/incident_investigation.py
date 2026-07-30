"""
Incident Investigation Agent.

Source of truth:
- docs/ShieldEPC_Architecture_Spec_v1.md §3 (Agent Roster), §6 (Zero
  Hallucination Policy)
- PHASE4_INCIDENT_INVESTIGATION_DESIGN.md (approved design checkpoint)

Phase 4 scope (first cut): RCA scaffolding only (5-Why, Fishbone,
Bowtie structuring). Historical pattern-match to past incidents is
explicitly out of scope — deferred to a later milestone that adds an
incident history persistence store.

Deterministic validation/composition only -- no LLM call, no generative
inference. The agent does not invent RCA content; the caller
(investigator) supplies structured findings and this agent validates
and organizes them into a fixed scaffold.

Blame-safety is structural, not prompt-based: no field in the request
or response schema is capable of naming or assigning fault to an
individual. FishboneCategory is a fixed enum of human-factors-style
categories (e.g. "people_factors"), never a named-person field.

Human sign-off is mandatory and cannot be set by this agent: every
response includes investigator_signoff with signed_off=False. Only a
separate, future sign-off workflow can complete it.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ValidationError, field_validator

from app.agents.base import Agent, InsufficientInformation


class FishboneCategory(str, Enum):
    PEOPLE_FACTORS = "people_factors"
    PROCESS = "process"
    EQUIPMENT = "equipment"
    MATERIALS = "materials"
    ENVIRONMENT = "environment"


class IncidentInvestigationRequest(BaseModel):
    incident_description: str
    five_whys: list[str]
    fishbone_causes: dict[FishboneCategory, list[str]]
    bowtie_top_event: str
    bowtie_threats: list[str]
    bowtie_consequences: list[str]
    preventive_barriers: list[str]
    mitigative_barriers: list[str]

    @field_validator("incident_description", "bowtie_top_event")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v

    @field_validator("five_whys")
    @classmethod
    def five_whys_non_empty_entries(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("five_whys must have at least one entry")
        if any(not entry.strip() for entry in v):
            raise ValueError("five_whys entries must not be blank")
        return v


class IncidentInvestigationAgent(Agent):
    """
    Validates and organizes investigator-supplied RCA findings (5-Why,
    Fishbone, Bowtie) into a fixed scaffold. See module docstring for
    the approved design boundary (no blame-capable fields, no
    generative content, mandatory unset human sign-off).
    """

    name = "incident_investigation_agent"
    version = "0.1.0"

    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        request must contain:
          - incident_description: str, non-empty
          - five_whys: list[str], non-empty, no blank entries
          - fishbone_causes: dict[FishboneCategory, list[str]]
          - bowtie_top_event: str, non-empty
          - bowtie_threats: list[str]
          - bowtie_consequences: list[str]
          - preventive_barriers: list[str]
          - mitigative_barriers: list[str]

        Raises InsufficientInformation if the request fails validation
        -- never fills a gap with a plausible-sounding default (spec §6
        point 4).
        """
        try:
            validated = IncidentInvestigationRequest(**request)
        except ValidationError as exc:
            raise InsufficientInformation(
                f"Invalid incident investigation request: {exc}"
            )

        fishbone_summary = {
            category.value: causes
            for category, causes in validated.fishbone_causes.items()
        }

        answer = (
            "DRAFT — PENDING HUMAN INVESTIGATOR SIGN-OFF\n"
            f"Incident: {validated.incident_description}\n"
            f"5-Why chain: {' -> '.join(validated.five_whys)}\n"
            f"Bowtie top event: {validated.bowtie_top_event}\n"
        )

        return {
            "answer": answer,
            "confidence_score": 1.0,
            "confidence_basis": (
                "Deterministic composition: investigator-supplied "
                "5-Why, Fishbone, and Bowtie findings were validated "
                "and organized into a fixed scaffold, with no "
                "generative inference or fault/blame attribution "
                "performed."
            ),
            "source_of_reasoning": [
                {
                    "type": "structured_input",
                    "ref": "investigator_supplied_findings:incident_investigation",
                }
            ],
            "missing_information": [],
            "assumptions_made": [],
            "applicable_standards": [],
            "five_whys": validated.five_whys,
            "fishbone_causes": fishbone_summary,
            "bowtie": {
                "top_event": validated.bowtie_top_event,
                "threats": validated.bowtie_threats,
                "consequences": validated.bowtie_consequences,
                "preventive_barriers": validated.preventive_barriers,
                "mitigative_barriers": validated.mitigative_barriers,
            },
            "investigator_signoff": {
                "investigator_id": None,
                "status": "pending",
                "signed_at": None,
            },
            "human_review_required": True,
            "human_review_reason": "statutory_requirement",
        }
