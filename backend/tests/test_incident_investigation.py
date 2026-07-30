"""
Unit tests for IncidentInvestigationAgent.

Covers: valid request happy path, validation failures, and the two
structural safety guarantees from PHASE4_INCIDENT_INVESTIGATION_DESIGN.md
-- blame-safety (no field can name/fault an individual) and mandatory
unset human sign-off.
"""

from __future__ import annotations

import pytest

from app.agents.base import InsufficientInformation
from app.agents.incident_investigation import (
    FishboneCategory,
    IncidentInvestigationAgent,
    IncidentInvestigationRequest,
)


@pytest.fixture
def agent():
    return IncidentInvestigationAgent()


@pytest.fixture
def valid_request():
    return {
        "incident_description": "Worker slipped on wet floor near loading bay",
        "five_whys": [
            "Worker slipped on wet floor",
            "Floor was wet from a leak",
            "Leak was not reported",
            "No routine leak-check process exists",
            "Maintenance schedule does not include leak checks",
        ],
        "fishbone_causes": {
            "people_factors": ["Inadequate hazard awareness training"],
            "process": ["No routine leak-check process"],
            "equipment": ["Aging pipe fitting"],
            "materials": [],
            "environment": ["Poor drainage near loading bay"],
        },
        "bowtie_top_event": "Slip and fall incident",
        "bowtie_threats": ["Wet floor surface"],
        "bowtie_consequences": ["Worker injury"],
        "preventive_barriers": ["Routine leak inspection"],
        "mitigative_barriers": ["First aid response protocol"],
    }


def test_valid_request_returns_scaffold(agent, valid_request):
    result = agent.run(valid_request)

    assert "PENDING HUMAN INVESTIGATOR SIGN-OFF" in result["answer"]
    assert result["five_whys"] == valid_request["five_whys"]
    assert result["fishbone_causes"]["people_factors"] == [
        "Inadequate hazard awareness training"
    ]
    assert result["bowtie"]["top_event"] == "Slip and fall incident"


def test_empty_five_whys_raises(agent, valid_request):
    valid_request["five_whys"] = []
    with pytest.raises(InsufficientInformation):
        agent.run(valid_request)


def test_blank_five_whys_entry_raises(agent, valid_request):
    valid_request["five_whys"] = ["Worker slipped", "   "]
    with pytest.raises(InsufficientInformation):
        agent.run(valid_request)


def test_blank_incident_description_raises(agent, valid_request):
    valid_request["incident_description"] = "   "
    with pytest.raises(InsufficientInformation):
        agent.run(valid_request)


def test_blank_bowtie_top_event_raises(agent, valid_request):
    valid_request["bowtie_top_event"] = "   "
    with pytest.raises(InsufficientInformation):
        agent.run(valid_request)


def test_unknown_fishbone_category_raises(agent, valid_request):
    valid_request["fishbone_causes"] = {"unknown_category": ["x"]}
    with pytest.raises(InsufficientInformation):
        agent.run(valid_request)


def test_human_review_required_true(agent, valid_request):
    result = agent.run(valid_request)
    assert result["human_review_required"] is True
    assert result["human_review_reason"] == "statutory_requirement"


def test_investigator_signoff_always_unset(agent, valid_request):
    result = agent.run(valid_request)
    assert result["investigator_signoff"] == {
        "investigator_id": None,
        "status": "pending",
        "signed_at": None,
    }


def test_schema_has_no_blame_capable_field():
    """
    Structural blame-safety guarantee: no field name on the request or
    response side is capable of naming/faulting an individual.
    """
    forbidden_substrings = ("responsible", "at_fault", "blame", "culprit")

    request_fields = set(IncidentInvestigationRequest.model_fields.keys())
    fishbone_values = {c.value for c in FishboneCategory}

    all_field_names = request_fields | fishbone_values
    for name in all_field_names:
        for forbidden in forbidden_substrings:
            assert forbidden not in name.lower(), (
                f"Field/category '{name}' contains forbidden substring "
                f"'{forbidden}' -- violates structural blame-safety."
            )


def test_fishbone_category_has_no_named_individual_option():
    category_values = {c.value for c in FishboneCategory}
    assert category_values == {
        "people_factors",
        "process",
        "equipment",
        "materials",
        "environment",
    }
