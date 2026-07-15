"""
Phase 3 Step 2 unit tests: PTWJSAAgent.

Run from backend/ with:

    python3 test_ptw_jsa.py
"""

from __future__ import annotations

import sys

from app.agents.base import InsufficientInformation
from app.agents.ptw_jsa import PTWJSAAgent


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
    agent = PTWJSAAgent()

    # 1. Valid JSA request
    jsa_result = agent.run(
        {
            "doc_type": "jsa",
            "location": "Zone 4",
            "date": "2026-07-15",
            "performed_by": "Test User",
            "task_description": "Excavation near buried services",
            "selected_hazard_ids": ["excavation", "confined_space"],
        }
    )
    check(
        "JOB SAFETY ANALYSIS" in jsa_result["answer"],
        "valid JSA request renders JSA template",
    )
    check(
        {h["hazard_id"] for h in jsa_result["identified_hazards"]}
        == {"excavation", "confined_space"},
        "JSA request identifies both requested hazards",
    )

    # 2. Valid PTW request
    ptw_result = agent.run(
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
    check(
        "PERMIT TO WORK" in ptw_result["answer"],
        "valid PTW request renders PTW template",
    )

    # 3. Missing PTW duration
    expect_insufficient_information(
        lambda: agent.run(
            {
                "doc_type": "ptw",
                "location": "Z",
                "date": "d",
                "performed_by": "p",
                "task_description": "t",
                "selected_hazard_ids": ["hot_work"],
            }
        ),
        "missing duration for ptw raises InsufficientInformation",
    )

    # 4. Unknown hazard
    expect_insufficient_information(
        lambda: agent.run(
            {
                "doc_type": "jsa",
                "location": "Z",
                "date": "d",
                "performed_by": "p",
                "task_description": "t",
                "selected_hazard_ids": ["nonexistent_hazard"],
            }
        ),
        "unknown hazard_id raises InsufficientInformation",
    )

    # 5. Invalid doc_type
    expect_insufficient_information(
        lambda: agent.run(
            {
                "doc_type": "invalid_type",
                "location": "Z",
                "date": "d",
                "performed_by": "p",
                "task_description": "t",
                "selected_hazard_ids": ["hot_work"],
            }
        ),
        "invalid doc_type raises InsufficientInformation",
    )

    # 6. Empty selected_hazard_ids
    expect_insufficient_information(
        lambda: agent.run(
            {
                "doc_type": "jsa",
                "location": "Z",
                "date": "d",
                "performed_by": "p",
                "task_description": "t",
                "selected_hazard_ids": [],
            }
        ),
        "empty selected_hazard_ids raises InsufficientInformation",
    )

    # 7. Blank task_description
    expect_insufficient_information(
        lambda: agent.run(
            {
                "doc_type": "jsa",
                "location": "Z",
                "date": "d",
                "performed_by": "p",
                "task_description": "   ",
                "selected_hazard_ids": ["hot_work"],
            }
        ),
        "blank task_description raises InsufficientInformation",
    )

    # 8. human_review_required is True
    check(
        jsa_result["human_review_required"] is True,
        "human_review_required is True (JSA)",
    )
    check(
        ptw_result["human_review_required"] is True,
        "human_review_required is True (PTW)",
    )

    # 9. human_review_reason is statutory_requirement
    check(
        jsa_result["human_review_reason"] == "statutory_requirement",
        "human_review_reason is statutory_requirement (JSA)",
    )
    check(
        ptw_result["human_review_reason"] == "statutory_requirement",
        "human_review_reason is statutory_requirement (PTW)",
    )

    # 10. source_of_reasoning contains both expected refs
    jsa_refs = {s["ref"] for s in jsa_result["source_of_reasoning"]}
    check(
        jsa_refs == {"caller_supplied_fields:jsa_draft", "tenant_hazard_library:selected_hazards"},
        "JSA source_of_reasoning contains both caller_supplied_fields and tenant_hazard_library refs",
    )
    ptw_refs = {s["ref"] for s in ptw_result["source_of_reasoning"]}
    check(
        ptw_refs == {"caller_supplied_fields:ptw_draft", "tenant_hazard_library:selected_hazards"},
        "PTW source_of_reasoning contains both caller_supplied_fields and tenant_hazard_library refs",
    )

    # Extra: confirm answer text is never contaminated with hazard/control
    # text -- the approved design boundary (no appending to DocumentGenerator
    # output).
    check(
        "Excavation permit issued" not in jsa_result["answer"],
        "JSA answer text is not contaminated with hazard control text",
    )

    print("\n✅ Phase 3 Step 2 PTWJSAAgent tests PASSED")


if __name__ == "__main__":
    main()
