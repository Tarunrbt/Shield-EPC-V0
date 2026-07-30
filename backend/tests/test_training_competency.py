"""
Unit tests for TrainingCompetencyAgent.

Covers: valid request happy path, gap detection (missing/expired/not
completed), validation failures, and the deterministic-output
guarantees from PHASE4B_TRAINING_COMPETENCY_DESIGN.md -- confidence
score always 1.0 and source_of_reasoning always a single
structured_input entry.
"""

from __future__ import annotations

import pytest

from app.agents.base import InsufficientInformation
from app.agents.training_competency import TrainingCompetencyAgent


@pytest.fixture
def agent():
    return TrainingCompetencyAgent()


@pytest.fixture
def valid_request():
    return {
        "role_or_task": "Confined space entry",
        "assessment_date": "2026-07-30",
        "required_competencies": [
            "Confined Space Entry Training",
            "First Aid Certification",
        ],
        "training_records": [
            {
                "competency_name": "Confined Space Entry Training",
                "completed": True,
                "completion_date": "2026-01-10",
                "expiry_date": "2027-01-10",
                "issuing_body": "Internal Safety Dept",
            },
            {
                "competency_name": "First Aid Certification",
                "completed": True,
                "completion_date": "2025-06-01",
                "expiry_date": "2027-06-01",
                "issuing_body": "Red Cross",
            },
        ],
    }


def test_valid_request_all_satisfied(agent, valid_request):
    result = agent.run(valid_request)

    assert "PENDING HUMAN REVIEW" in result["answer"]
    assert result["missing_information"] == []
    assert result["human_review_reason"] == "statutory_requirement"


def test_missing_competency_reported(agent, valid_request):
    valid_request["training_records"] = [
        valid_request["training_records"][0]
    ]  # drop First Aid record

    result = agent.run(valid_request)

    assert any(
        "missing: First Aid Certification" in entry
        for entry in result["missing_information"]
    )
    assert result["human_review_reason"] == "compliance_gap_flagged"


def test_expired_competency_reported(agent, valid_request):
    valid_request["training_records"][0]["expiry_date"] = "2026-01-01"

    result = agent.run(valid_request)

    assert any(
        "expired: Confined Space Entry Training" in entry
        for entry in result["missing_information"]
    )
    assert result["human_review_reason"] == "compliance_gap_flagged"


def test_not_completed_treated_as_gap(agent, valid_request):
    valid_request["training_records"][0]["completed"] = False

    result = agent.run(valid_request)

    assert any(
        "missing: Confined Space Entry Training" in entry
        for entry in result["missing_information"]
    )
    assert result["human_review_reason"] == "compliance_gap_flagged"


def test_blank_role_or_task_raises(agent, valid_request):
    valid_request["role_or_task"] = "   "
    with pytest.raises(InsufficientInformation):
        agent.run(valid_request)


def test_blank_assessment_date_raises(agent, valid_request):
    valid_request["assessment_date"] = "   "
    with pytest.raises(InsufficientInformation):
        agent.run(valid_request)


def test_empty_required_competencies_raises(agent, valid_request):
    valid_request["required_competencies"] = []
    with pytest.raises(InsufficientInformation):
        agent.run(valid_request)


def test_blank_required_competency_entry_raises(agent, valid_request):
    valid_request["required_competencies"] = ["Confined Space Entry Training", "   "]
    with pytest.raises(InsufficientInformation):
        agent.run(valid_request)


def test_blank_competency_name_in_record_raises(agent, valid_request):
    valid_request["training_records"][0]["competency_name"] = "   "
    with pytest.raises(InsufficientInformation):
        agent.run(valid_request)


def test_unparseable_assessment_date_raises(agent, valid_request):
    valid_request["assessment_date"] = "not-a-date"
    with pytest.raises(InsufficientInformation):
        agent.run(valid_request)


def test_unparseable_expiry_date_raises(agent, valid_request):
    valid_request["training_records"][0]["expiry_date"] = "not-a-date"
    with pytest.raises(InsufficientInformation):
        agent.run(valid_request)


def test_confidence_score_always_one(agent, valid_request):
    result = agent.run(valid_request)
    assert result["confidence_score"] == 1.0


def test_source_of_reasoning_single_structured_input(agent, valid_request):
    result = agent.run(valid_request)
    assert len(result["source_of_reasoning"]) == 1
    assert result["source_of_reasoning"][0]["type"] == "structured_input"


def test_human_review_required_always_true(agent, valid_request):
    result = agent.run(valid_request)
    assert result["human_review_required"] is True
