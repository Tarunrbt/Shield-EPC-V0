"""
Phase 3 Step 1 unit tests: RiskAssessmentAgent.

Run from backend/ with:

    python3 test_risk_assessment.py
"""

from __future__ import annotations

import sys

from app.agents.base import InsufficientInformation
from app.agents.risk_assessment import RiskAssessmentAgent


def check(condition: bool, message: str) -> None:
    if not condition:
        print(f"FAIL: {message}")
        sys.exit(1)
    print(f"OK:   {message}")


def expect_insufficient_information(fn, message: str) -> None:
    try:
        fn()
    except InsufficientInformation:
        print(f"OK:   {message}")
    else:
        print(f"FAIL: {message} (no exception raised)")
        sys.exit(1)


def main() -> None:
    agent = RiskAssessmentAgent()

    # 1. Valid request, single hazard
    result = agent.run(
        {
            "task_description": "Excavation near buried services",
            "selected_hazard_ids": ["excavation"],
            "likelihood": 2,
            "severity": 3,
        }
    )
    check(bool(result["answer"]), "valid request produces non-empty answer")
    check(result["risk_score"] == 6, "risk_score == likelihood * severity (2*3=6)")
    check(result["risk_level"] is None, "risk_level is None")
    check(result["human_review_required"] is True, "human_review_required is True")
    check(
        result["human_review_reason"] == "statutory_requirement",
        "human_review_reason is statutory_requirement",
    )
    check(
        result["source_of_reasoning"]
        == [
            {
                "type": "structured_input",
                "ref": "tenant_hazard_library:selected_hazards",
            }
        ],
        "source_of_reasoning matches tenant_hazard_library:selected_hazards",
    )
    check(
        [h["hazard_id"] for h in result["identified_hazards"]] == ["excavation"],
        "identified_hazards contains the single requested hazard",
    )

    # 2. Unknown hazard -> InsufficientInformation
    expect_insufficient_information(
        lambda: agent.run(
            {
                "task_description": "Test",
                "selected_hazard_ids": ["nonexistent_hazard"],
                "likelihood": 3,
                "severity": 3,
            }
        ),
        "unknown hazard_id raises InsufficientInformation",
    )

    # 3. Invalid likelihood (out of 1-5 range)
    expect_insufficient_information(
        lambda: agent.run(
            {
                "task_description": "Test",
                "selected_hazard_ids": ["hot_work"],
                "likelihood": 9,
                "severity": 3,
            }
        ),
        "likelihood out of range raises InsufficientInformation",
    )

    # 4. Invalid severity (out of 1-5 range)
    expect_insufficient_information(
        lambda: agent.run(
            {
                "task_description": "Test",
                "selected_hazard_ids": ["hot_work"],
                "likelihood": 3,
                "severity": 0,
            }
        ),
        "severity out of range raises InsufficientInformation",
    )

    # 5. Empty hazard list
    expect_insufficient_information(
        lambda: agent.run(
            {
                "task_description": "Test",
                "selected_hazard_ids": [],
                "likelihood": 3,
                "severity": 3,
            }
        ),
        "empty selected_hazard_ids raises InsufficientInformation",
    )

    # 6. Blank task_description
    expect_insufficient_information(
        lambda: agent.run(
            {
                "task_description": "   ",
                "selected_hazard_ids": ["hot_work"],
                "likelihood": 3,
                "severity": 3,
            }
        ),
        "blank task_description raises InsufficientInformation",
    )

    # 7. Multiple hazards merge correctly
    multi_result = agent.run(
        {
            "task_description": "Welding at height near open excavation",
            "selected_hazard_ids": ["work_at_height", "hot_work", "excavation"],
            "likelihood": 4,
            "severity": 5,
        }
    )
    check(
        {h["hazard_id"] for h in multi_result["identified_hazards"]}
        == {"work_at_height", "hot_work", "excavation"},
        "multiple hazards all identified",
    )
    check(multi_result["risk_score"] == 20, "risk_score == 4*5 for multi-hazard request")

    # 8. Deduplication of controls/PPE/standards
    # work_at_height and hot_work and excavation all include "ISO 45001:2018"
    # in applicable_standards -- must appear exactly once after dedup.
    standards = multi_result["applicable_standards"]
    check(
        standards.count("ISO 45001:2018") == 1,
        "applicable_standards deduplicated (ISO 45001:2018 appears once)",
    )
    controls = multi_result["recommended_controls"]
    check(
        len(controls) == len(set(controls)),
        "recommended_controls contains no duplicate entries",
    )
    ppe = multi_result["required_ppe"]
    check(
        len(ppe) == len(set(ppe)),
        "required_ppe contains no duplicate entries",
    )

    # 9 & 10 already covered above for the single-hazard case, re-check on
    # the multi-hazard result too for extra confidence.
    check(
        multi_result["human_review_required"] is True,
        "human_review_required is True (multi-hazard)",
    )
    check(
        multi_result["risk_level"] is None,
        "risk_level is None (multi-hazard)",
    )

    print("\n✅ Phase 3 Step 1 RiskAssessmentAgent tests PASSED")


if __name__ == "__main__":
    main()
