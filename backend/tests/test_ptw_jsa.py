"""
PTWJSAAgent tests (pytest version).

Migrated from the standalone test_ptw_jsa.py script (Phase 3 Step 2) so
these run under `pytest -q` and are counted in the regular suite. Same
coverage as the original script -- no new assertions added, no existing
ones removed.
"""

from __future__ import annotations

import pytest

from app.agents.base import InsufficientInformation
from app.agents.ptw_jsa import PTWJSAAgent


@pytest.fixture
def agent():
    return PTWJSAAgent()


@pytest.fixture
def jsa_result(agent):
    return agent.run(
        {
            "doc_type": "jsa",
            "location": "Zone 4",
            "date": "2026-07-15",
            "performed_by": "Test User",
            "task_description": "Excavation near buried services",
            "selected_hazard_ids": ["excavation", "confined_space"],
        }
    )


@pytest.fixture
def ptw_result(agent):
    return agent.run(
        {
            "doc_type": "ptw",
            "location": "Zone 4",
            "date": "2026-07-15",
            "performed_by": "Test User",
            "task_description": "Hot work on pipe rack",
            "selected_hazard_ids": ["hot_work"],
            "duration": "4 hours",
        }
    )


def test_valid_jsa_request_renders_jsa_template(jsa_result):
    assert "JOB SAFETY ANALYSIS" in jsa_result["answer"]


def test_valid_jsa_request_identifies_both_hazards(jsa_result):
    hazard_ids = {h["hazard_id"] for h in jsa_result["identified_hazards"]}
    assert hazard_ids == {"excavation", "confined_space"}


def test_valid_ptw_request_renders_ptw_template(ptw_result):
    assert "PERMIT TO WORK" in ptw_result["answer"]


def test_missing_duration_for_ptw_raises(agent):
    with pytest.raises(InsufficientInformation):
        agent.run(
            {
                "doc_type": "ptw",
                "location": "Z",
                "date": "d",
                "performed_by": "p",
                "task_description": "t",
                "selected_hazard_ids": ["hot_work"],
            }
        )


def test_unknown_hazard_id_raises(agent):
    with pytest.raises(InsufficientInformation):
        agent.run(
            {
                "doc_type": "jsa",
                "location": "Z",
                "date": "d",
                "performed_by": "p",
                "task_description": "t",
                "selected_hazard_ids": ["nonexistent_hazard"],
            }
        )


def test_invalid_doc_type_raises(agent):
    with pytest.raises(InsufficientInformation):
        agent.run(
            {
                "doc_type": "invalid_type",
                "location": "Z",
                "date": "d",
                "performed_by": "p",
                "task_description": "t",
                "selected_hazard_ids": ["hot_work"],
            }
        )


def test_empty_selected_hazard_ids_raises(agent):
    with pytest.raises(InsufficientInformation):
        agent.run(
            {
                "doc_type": "jsa",
                "location": "Z",
                "date": "d",
                "performed_by": "p",
                "task_description": "t",
                "selected_hazard_ids": [],
            }
        )


def test_blank_task_description_raises(agent):
    with pytest.raises(InsufficientInformation):
        agent.run(
            {
                "doc_type": "jsa",
                "location": "Z",
                "date": "d",
                "performed_by": "p",
                "task_description": "   ",
                "selected_hazard_ids": ["hot_work"],
            }
        )


def test_human_review_required_true_jsa(jsa_result):
    assert jsa_result["human_review_required"] is True


def test_human_review_required_true_ptw(ptw_result):
    assert ptw_result["human_review_required"] is True


def test_human_review_reason_statutory_jsa(jsa_result):
    assert jsa_result["human_review_reason"] == "statutory_requirement"


def test_human_review_reason_statutory_ptw(ptw_result):
    assert ptw_result["human_review_reason"] == "statutory_requirement"


def test_jsa_source_of_reasoning_contains_expected_refs(jsa_result):
    refs = {s["ref"] for s in jsa_result["source_of_reasoning"]}
    assert refs == {
        "caller_supplied_fields:jsa_draft",
        "tenant_hazard_library:selected_hazards",
    }


def test_ptw_source_of_reasoning_contains_expected_refs(ptw_result):
    refs = {s["ref"] for s in ptw_result["source_of_reasoning"]}
    assert refs == {
        "caller_supplied_fields:ptw_draft",
        "tenant_hazard_library:selected_hazards",
    }


def test_jsa_answer_not_contaminated_with_hazard_control_text(jsa_result):
    # Approved design boundary (PHASE3_PTWJSA_DESIGN.md): no appending
    # hazard/control text into DocumentGeneratorAgent's rendered output.
    assert "Excavation permit issued" not in jsa_result["answer"]
