"""
Standard Clause data model.

Source of truth: docs/ShieldEPC_Architecture_Spec_v1.md §6 (Zero
Hallucination Policy) and the Phase 4 Milestone 4.1 locked design.

StandardClause is intentionally minimal and immutable -- it is a pure
data record, not a computation. It mirrors the pattern already
established by app.hazards.library.Hazard: frozen so no downstream
code can mutate a shared clause instance, and slotted so instances
stay lightweight since many are held in the read-only library.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StandardClause:
    """
    One clause of one named standard, scoped to the hazard_ids it
    applies to.

    applicable_hazard_ids must only reference hazard_ids that already
    exist in app.hazards.library.HAZARD_CATALOG -- this module does
    not define a second hazard vocabulary. Validation of that
    constraint happens in app.standards.resolver, not here; this is a
    plain data record with no behavior.
    """

    clause_id: str
    standard_name: str
    clause_reference: str
    requirement_summary: str
    applicable_hazard_ids: tuple[str, ...]
