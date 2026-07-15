"""Standards Clause Library package.

Exposes StandardClause and the resolver's public functions only.
app.standards.library's underlying mapping is intentionally not
re-exported here -- resolver-only access, per the Phase 4 Milestone
4.1 locked design.
"""

from app.standards.models import StandardClause
from app.standards.resolver import (
    get_clause,
    get_clauses,
    get_clauses_for_hazard,
    get_clauses_for_standard,
)

__all__ = [
    "StandardClause",
    "get_clause",
    "get_clauses",
    "get_clauses_for_hazard",
    "get_clauses_for_standard",
]
