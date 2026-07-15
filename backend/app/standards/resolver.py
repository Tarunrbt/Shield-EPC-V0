"""
Standards Clause Resolver.
Phase 4, Milestone 4.1 (locked design, resolver-only access)

Sole read access point for app.standards.library's _STANDARD_LIBRARY.
Future callers (e.g. the ComplianceAgent planned for Milestone 4.2)
must go through these functions rather than importing the private
mapping directly.

Deterministic lookup only -- no generative inference, no clause
interpretation, no keyword search (deferred to a future milestone).
Unknown clause_id, unknown standard_name, or unknown hazard_id raises
app.agents.base.InsufficientInformation, matching the Zero
Hallucination Policy already enforced by app.hazards.library. No new
exception classes are introduced.
"""

from __future__ import annotations

from app.agents.base import InsufficientInformation
from app.hazards.library import get_hazard
from app.standards.library import _STANDARD_LIBRARY
from app.standards.models import StandardClause

_STANDARD_NAMES: frozenset[str] = frozenset(
    clause.standard_name for clause in _STANDARD_LIBRARY.values()
)


def get_clause(clause_id: str) -> StandardClause:
    """Return the clause for clause_id, or raise InsufficientInformation."""
    try:
        return _STANDARD_LIBRARY[clause_id]
    except KeyError:
        raise InsufficientInformation(
            f"Unknown clause_id '{clause_id}': not present in standards library"
        )


def get_clauses(clause_ids: tuple[str, ...]) -> tuple[StandardClause, ...]:
    """
    Return the clauses for clause_ids, deduplicated and order-preserved.

    Any unknown clause_id raises InsufficientInformation via
    get_clause. Deduplication guarantees this never returns duplicate
    clause matches, even if the caller passes the same clause_id more
    than once.
    """
    seen: set[str] = set()
    result: list[StandardClause] = []
    for clause_id in clause_ids:
        if clause_id in seen:
            continue
        seen.add(clause_id)
        result.append(get_clause(clause_id))
    return tuple(result)


def get_clauses_for_standard(standard_name: str) -> tuple[StandardClause, ...]:
    """
    Return every clause belonging to standard_name.

    Raises InsufficientInformation if standard_name is not present in
    the standards library at all.
    """
    if standard_name not in _STANDARD_NAMES:
        raise InsufficientInformation(
            f"Unknown standard '{standard_name}': not present in standards library"
        )
    return tuple(
        clause
        for clause in _STANDARD_LIBRARY.values()
        if clause.standard_name == standard_name
    )


def get_clauses_for_hazard(hazard_id: str) -> tuple[StandardClause, ...]:
    """
    Return every clause applicable to hazard_id.

    hazard_id is validated against app.hazards.library.HAZARD_CATALOG
    (via get_hazard) rather than against a second, standards-local
    vocabulary -- the tenant hazard library remains the single source
    of truth for hazard_ids. Unknown hazard_id raises
    InsufficientInformation from that existing call.
    """
    get_hazard(hazard_id)
    return tuple(
        clause
        for clause in _STANDARD_LIBRARY.values()
        if hazard_id in clause.applicable_hazard_ids
    )
