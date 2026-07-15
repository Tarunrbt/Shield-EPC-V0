"""
Phase 4 Milestone 4.2 unit tests: ComplianceAgent.

Run from backend/ with:

    python3 test_compliance.py
"""

from __future__ import annotations

import sys

from app.agents.base import InsufficientInformation
from app.agents.compliance import ComplianceAgent


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
    agent = ComplianceAgent()

    # 1. Valid request, two standards, one hazard -> two matched clauses
    result = agent.run(
        {
            "standard_ids": ["ISO 45001:2018", "BOCW Act 1996, Regulation 116"],
            "jurisdiction": "India",
            "selected_hazard_ids": ["work_at_height"],
        }
    )
    check(bool(result["answer"]), "valid request produces non-empty answer")
    check(
        len(result["applicable_clauses"]) == 2,
        "valid request resolves both applicable clauses",
    )
    clause_ids = {c["clause_id"] for c in result["applicable_clauses"]}
    check(
        clause_ids == {"iso45001-work-at-height", "bocw-reg116-work-at-height"},
        "valid request resolves the expected clause_ids",
    )
    check(result["missing_requirements"] == [], "no missing_requirements for a full match")

    # 2. Unknown standard -> InsufficientInformation
    expect_insufficient_information(
        lambda: agent.run(
            {
                "standard_ids": ["Made Up Standard 9999"],
                "jurisdiction": "India",
                "selected_hazard_ids": ["work_at_height"],
            }
        ),
        "unknown standard raises InsufficientInformation",
    )

    # 3. Unknown hazard -> InsufficientInformation
    expect_insufficient_information(
        lambda: agent.run(
            {
                "standard_ids": ["ISO 45001:2018"],
                "jurisdiction": "India",
                "selected_hazard_ids": ["nonexistent_hazard"],
            }
        ),
        "unknown hazard raises InsufficientInformation",
    )

    # 4. Blank jurisdiction -> InsufficientInformation
    expect_insufficient_information(
        lambda: agent.run(
            {
                "standard_ids": ["ISO 45001:2018"],
                "jurisdiction": "   ",
                "selected_hazard_ids": ["work_at_height"],
            }
        ),
        "blank jurisdiction raises InsufficientInformation",
    )

    # 5. Empty standard_ids -> InsufficientInformation
    expect_insufficient_information(
        lambda: agent.run(
            {
                "standard_ids": [],
                "jurisdiction": "India",
                "selected_hazard_ids": ["work_at_height"],
            }
        ),
        "empty standard_ids raises InsufficientInformation",
    )

    # 6. Empty selected_hazard_ids -> InsufficientInformation
    expect_insufficient_information(
        lambda: agent.run(
            {
                "standard_ids": ["ISO 45001:2018"],
                "jurisdiction": "India",
                "selected_hazard_ids": [],
            }
        ),
        "empty selected_hazard_ids raises InsufficientInformation",
    )

    # 7. No duplicate clauses: repeated standard_ids/hazard_ids in the
    #    request still produce unique clause_ids in the output
    dup_result = agent.run(
        {
            "standard_ids": ["ISO 45001:2018", "ISO 45001:2018"],
            "jurisdiction": "India",
            "selected_hazard_ids": ["work_at_height", "work_at_height"],
        }
    )
    check(
        len(dup_result["applicable_clauses"]) == 1,
        "duplicate standard_ids/hazard_ids do not duplicate matched clauses",
    )
    dup_ids = [c["clause_id"] for c in dup_result["applicable_clauses"]]
    check(len(dup_ids) == len(set(dup_ids)), "no duplicate clause_id in applicable_clauses")

    # 8. source_of_reasoning is the locked, deterministic grounding
    check(
        result["source_of_reasoning"]
        == [
            {
                "type": "structured_input",
                "ref": "standards_library:selected_clauses",
            }
        ],
        "source_of_reasoning matches the locked deterministic grounding",
    )

    # 9. human_review_required / human_review_reason
    check(result["human_review_required"] is True, "human_review_required is True")
    check(
        result["human_review_reason"] == "statutory_requirement",
        "human_review_reason is statutory_requirement",
    )

    # 10. confidence_score
    check(result["confidence_score"] == 1.0, "confidence_score == 1.0")

    # Bonus: partial match populates missing_requirements honestly
    # instead of fabricating a clause that doesn't exist.
    partial = agent.run(
        {
            "standard_ids": ["Factories Act 1948, Section 36"],
            "jurisdiction": "India",
            "selected_hazard_ids": ["work_at_height"],
        }
    )
    check(
        partial["applicable_clauses"] == [],
        "standard/hazard combination with no match returns no clauses",
    )
    check(
        len(partial["missing_requirements"]) == 1,
        "unmatched hazard is reported in missing_requirements",
    )

    print("\nAll Phase 4 Milestone 4.2 compliance tests passed.")


if __name__ == "__main__":
    main()
