"""
Phase 4 Milestone 4.1 unit tests: standards clause library + resolver.

Run from backend/ with:

    python3 test_standards.py
"""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError

from app.agents.base import InsufficientInformation
from app.standards import (
    StandardClause,
    get_clause,
    get_clauses,
    get_clauses_for_hazard,
    get_clauses_for_standard,
)


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
    # 1. Known clause_id resolves
    clause = get_clause("iso45001-work-at-height")
    check(isinstance(clause, StandardClause), "get_clause returns a StandardClause")
    check(clause.standard_name == "ISO 45001:2018", "clause has expected standard_name")
    check(
        "work_at_height" in clause.applicable_hazard_ids,
        "clause references the reused hazard_id work_at_height",
    )

    # 2. Unknown clause_id -> InsufficientInformation
    expect_insufficient_information(
        lambda: get_clause("nonexistent-clause"),
        "unknown clause_id raises InsufficientInformation",
    )

    # 3. Unknown standard -> InsufficientInformation
    expect_insufficient_information(
        lambda: get_clauses_for_standard("Made Up Standard 9999"),
        "unknown standard raises InsufficientInformation",
    )

    # 4. Known standard resolves and only contains that standard's clauses
    iso_clauses = get_clauses_for_standard("ISO 45001:2018")
    check(len(iso_clauses) > 0, "known standard returns at least one clause")
    check(
        all(c.standard_name == "ISO 45001:2018" for c in iso_clauses),
        "get_clauses_for_standard only returns matching clauses",
    )

    # 5. Unknown hazard_id -> InsufficientInformation (reuses hazard library)
    expect_insufficient_information(
        lambda: get_clauses_for_hazard("nonexistent_hazard"),
        "unknown hazard_id raises InsufficientInformation",
    )

    # 6. Known hazard_id resolves to only its own clauses
    for hazard_id in (
        "work_at_height",
        "hot_work",
        "confined_space",
        "lifting_operations",
        "electrical_isolation",
        "excavation",
    ):
        clauses = get_clauses_for_hazard(hazard_id)
        check(len(clauses) > 0, f"{hazard_id} resolves to at least one clause")
        check(
            all(hazard_id in c.applicable_hazard_ids for c in clauses),
            f"{hazard_id} clauses all reference {hazard_id}",
        )

    # 7. No duplicate clause matches: repeated clause_id input is deduplicated
    deduped = get_clauses(
        ("iso45001-work-at-height", "iso45001-work-at-height", "bocw-reg116-work-at-height")
    )
    check(len(deduped) == 2, "get_clauses deduplicates repeated clause_ids")
    ids_seen = [c.clause_id for c in deduped]
    check(len(ids_seen) == len(set(ids_seen)), "no duplicate clause_id in resolver output")

    # 8. get_clauses still raises on any unknown id in the batch
    expect_insufficient_information(
        lambda: get_clauses(("iso45001-work-at-height", "nonexistent-clause")),
        "get_clauses raises InsufficientInformation on unknown id in batch",
    )

    # 9. Public resolver contract is read-only: resolver functions return
    #    tuples (no append/item-assignment), and repeated calls return
    #    unchanged data, showing nothing mutated the library in between.
    result_a = get_clauses_for_hazard("work_at_height")
    check(isinstance(result_a, tuple), "get_clauses_for_hazard returns a tuple")
    try:
        result_a.append(clause)  # type: ignore[attr-defined]
    except AttributeError:
        print("OK:   resolver's tuple return type has no mutation methods")
    else:
        print("FAIL: resolver's tuple return type allowed append")
        sys.exit(1)
    result_b = get_clauses_for_hazard("work_at_height")
    check(result_a == result_b, "repeated resolver calls return unchanged data")

    # 10. Frozen dataclass prevents mutation of a StandardClause instance
    try:
        clause.standard_name = "Tampered Standard"  # type: ignore[misc]
    except FrozenInstanceError:
        print("OK:   frozen dataclass blocks attribute mutation")
    else:
        print("FAIL: frozen dataclass did not block attribute mutation")
        sys.exit(1)

    print("\nAll Phase 4 Milestone 4.1 standards tests passed.")


if __name__ == "__main__":
    main()
