"""
Dataclass entities for Shield EPC operational persistence.

Plain dataclasses, not Pydantic models -- these are persistence-layer
entities, not the API request/response boundary (that's what
app/envelope/schema.py is for). Mirrors the existing AuditEntry pattern in
app/audit/log.py for consistency.

Phase 2 scope: schema + entity shape only. No repository CRUD
implementation yet -- that's the next persistence phase.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Tenant:
    tenant_id: str
    name: str
    status: str  # e.g. "active", "suspended"
    created_at: str  # UTC ISO 8601, matches AuditEntry.timestamp convention


@dataclass
class Project:
    project_id: str
    tenant_id: str
    name: str
    created_at: str  # UTC ISO 8601
