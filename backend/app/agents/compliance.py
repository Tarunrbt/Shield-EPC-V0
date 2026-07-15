"""
Compliance Agent.

Source of truth:
- docs/ShieldEPC_Architecture_Spec_v1.md §3 (Agent Roster), §6 (Zero
  Hallucination Policy)
- Phase 4 Milestone 4.1 locked design (Standards Clause Library)
- Phase 4 Milestone 4.2 locked design (this agent)

Phase 4 Milestone 4.2 scope: for a caller-supplied set of standard
names and tenant-hazard-library hazard_ids, resolves which standards
clauses apply, using app.standards.resolver exclusively -- this agent
never imports app.standards.library directly (resolver-only access,
per the Phase 4 Milestone 4.1 locked design carried forward here).

Deterministic lookup and set-intersection only -- no generative
inference, no clause interpretation, no free-text fallback, no LLM
call. Unknown standard names or unknown hazard_ids raise
InsufficientInformation via the resolver, per base.py's contract.

Out of scope for this milestone: Orchestrator routing and API wiring
(added in a later milestone once this agent's unit tests are green).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError, field_validator

from app.agents.base import Agent, InsufficientInformation
from app.standards import StandardClause, get_clauses_for_hazard, get_clauses_for_standard


class ComplianceRequest(BaseModel):
    standard_ids: list[str]
    jurisdiction: str
    selected_hazard_ids: list[str]

    @field_validator("standard_ids")
    @classmethod
    def standard_ids_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("standard_ids must not be empty")
        return v

    @field_validator("selected_hazard_ids")
    @classmethod
    def hazard_ids_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("selected_hazard_ids must not be empty")
        return v

    @field_validator("jurisdiction")
    @classmethod
    def jurisdiction_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("jurisdiction must not be blank")
        return v


def _dedupe_clauses_preserve_order(
    clauses: tuple[StandardClause, ...]
) -> list[StandardClause]:
    seen: set[str] = set()
    result: list[StandardClause] = []
    for clause in clauses:
        if clause.clause_id not in seen:
            seen.add(clause.clause_id)
            result.append(clause)
    return result


class ComplianceAgent(Agent):
    """
    Resolves which standards-library clauses apply to a set of tenant
    hazard_ids, restricted to a caller-supplied set of standard names.

    All clause access goes through app.standards.resolver -- this
    agent holds no clause data of its own and performs no matching
    logic beyond set intersection on data the resolver already
    validated. jurisdiction is captured for traceability only;
    jurisdiction-based clause filtering does not exist in the
    standards library yet and is not fabricated here.
    """

    name = "compliance_agent"
    version = "0.1.0"

    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        request must contain:
          - standard_ids: list[str], non-empty, each must be a
            standard_name present in the standards library
          - jurisdiction: str, non-blank
          - selected_hazard_ids: list[str], non-empty, must exist in
            the tenant hazard library

        Raises InsufficientInformation if the request fails validation,
        if any standard_ids entry is not a known standard_name, or if
        any selected_hazard_ids entry is not present in the tenant
        hazard library -- never fills a gap with a plausible-sounding
        default (spec §6 point 4).
        """
        try:
            validated = ComplianceRequest(**request)
        except ValidationError as exc:
            raise InsufficientInformation(
                f"Invalid compliance request: {exc}"
            )

        standard_set = set(validated.standard_ids)

        # Validate every standard_id is a known standard_name. Unused
        # return value -- this call exists purely so an unknown
        # standard raises InsufficientInformation before any matching
        # happens, exactly as get_clauses_for_hazard does for hazards
        # below.
        for standard_name in standard_set:
            get_clauses_for_standard(standard_name)

        # Validate every hazard_id and collect its clauses in one pass.
        # Dict keys naturally dedupe repeated hazard_ids in the input.
        hazard_clause_map: dict[str, tuple[StandardClause, ...]] = {
            hazard_id: get_clauses_for_hazard(hazard_id)
            for hazard_id in validated.selected_hazard_ids
        }

        matched: list[StandardClause] = []
        missing_requirements: list[str] = []
        for hazard_id, clauses in hazard_clause_map.items():
            hazard_matches = [c for c in clauses if c.standard_name in standard_set]
            if not hazard_matches:
                missing_requirements.append(
                    f"No clause found in selected standards for "
                    f"hazard_id '{hazard_id}'"
                )
            matched.extend(hazard_matches)

        matched_clauses = _dedupe_clauses_preserve_order(tuple(matched))

        applicable_clauses = [
            {
                "clause_id": c.clause_id,
                "standard_name": c.standard_name,
                "clause_reference": c.clause_reference,
                "requirement_summary": c.requirement_summary,
            }
            for c in matched_clauses
        ]

        compliance_notes = [
            f"Jurisdiction '{validated.jurisdiction}' recorded for "
            f"traceability; jurisdiction-based clause filtering is not "
            f"yet implemented (deferred to a future milestone)."
        ]

        if matched_clauses:
            clause_lines = "\n".join(
                f"{c.standard_name} {c.clause_reference}" for c in matched_clauses
            )
            answer = f"Applicable clauses:\n{clause_lines}"
        else:
            answer = (
                "No applicable clauses found for the selected standards "
                "and hazards."
            )

        return {
            "answer": answer,
            "confidence_score": 1.0,
            "confidence_basis": (
                "Deterministic lookup: all standard_ids and hazard_ids "
                "were resolved exclusively through app.standards.resolver "
                "and app.hazards.library, and clauses were matched by set "
                "intersection with no generative inference or clause "
                "interpretation performed."
            ),
            "source_of_reasoning": [
                {
                    "type": "structured_input",
                    "ref": "standards_library:selected_clauses",
                }
            ],
            "missing_information": [],
            "assumptions_made": [],
            "applicable_clauses": applicable_clauses,
            "compliance_notes": compliance_notes,
            "missing_requirements": missing_requirements,
            "human_review_required": True,
            "human_review_reason": "statutory_requirement",
        }
