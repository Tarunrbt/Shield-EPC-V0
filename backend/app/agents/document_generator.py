"""
Document Generator Agent.

Source of truth: docs/ShieldEPC_Architecture_Spec_v1.md §3 (Agent Roster)
and ROADMAP.md Phase 1 ("chosen first because it's the least ambiguous
domain -- drafting from structured input, no judgment calls").

Phase 1 scope: fills a fixed template from caller-supplied structured
fields. Deterministic string substitution only -- no generative
inference, no clause interpretation. If a required field is missing,
this agent raises InsufficientInformation rather than guessing a
placeholder value, per base.py's contract and spec §6 point 4.

Templates are intentionally generic scaffolding, not real HSE content --
actual JSA/PTW clause language and required-field sets need domain
review before this is used on a real task. See the ASSUMPTIONS block
below for exactly what still needs confirming.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import Agent, InsufficientInformation

# ASSUMPTIONS (flagged, not verified against a real JSA/PTW spec):
# - required_fields lists here are placeholders illustrating the
#   mechanism, not a vetted list of what a real JSA/PTW must contain.
# - Real templates should likely be loaded from a template store /
#   tenant-configurable source, not hardcoded here, once Phase 2+
#   multi-tenancy work begins.
_TEMPLATES: dict[str, dict[str, Any]] = {
    "jsa_draft": {
        "required_fields": ["task_description", "location", "performed_by", "date"],
        "body": (
            "JOB SAFETY ANALYSIS (DRAFT)\n"
            "Task: {task_description}\n"
            "Location: {location}\n"
            "Performed by: {performed_by}\n"
            "Date: {date}\n"
        ),
    },
    "ptw_draft": {
        "required_fields": ["work_description", "location", "requested_by", "date", "duration"],
        "body": (
            "PERMIT TO WORK (DRAFT)\n"
            "Work: {work_description}\n"
            "Location: {location}\n"
            "Requested by: {requested_by}\n"
            "Date: {date}\n"
            "Duration: {duration}\n"
        ),
    },
}


class DocumentGeneratorAgent(Agent):
    """
    Fills a fixed template from structured fields. See module docstring
    for what is and is not yet verified about the templates themselves.
    """

    name = "document_generator_agent"
    version = "0.1.0"

    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        request must contain:
          - template_id: str, one of _TEMPLATES
          - fields: dict[str, str], values for that template's placeholders

        Raises InsufficientInformation if template_id is unknown or any
        required field is missing/empty -- never fills a gap with a
        plausible-sounding default (spec §6 point 4).
        """
        template_id = request.get("template_id")
        fields = request.get("fields", {})

        if template_id not in _TEMPLATES:
            raise InsufficientInformation(
                f"Unknown template_id '{template_id}'. Known templates: "
                f"{sorted(_TEMPLATES.keys())}"
            )

        template = _TEMPLATES[template_id]
        missing = [
            f for f in template["required_fields"]
            if not fields.get(f)
        ]
        if missing:
            raise InsufficientInformation(
                f"Missing required fields for template '{template_id}': {missing}"
            )

        answer = template["body"].format(**fields)

        return {
            "answer": answer,
            "confidence_score": 1.0,
            "confidence_basis": (
                "Deterministic template render: all required fields were "
                "present in the input and substituted directly, with no "
                "generative inference or clause interpretation performed."
            ),
            "source_of_reasoning": [],
            "missing_information": [],
            "assumptions_made": [],
            "applicable_standards": [],
            # ASSUMPTION, not verified against spec: every generated
            # document requires human sign-off before use, since this is
            # a draft feeding into a safety-critical document. Using
            # "statutory_requirement" as the closest fit among the four
            # allowed HumanReviewReason values -- confirm this is the
            # correct one, or whether Document Generator output should
            # ever bypass review.
            "human_review_required": True,
            "human_review_reason": "statutory_requirement",
        }

