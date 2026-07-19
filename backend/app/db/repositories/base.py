"""
Abstract repository contract for operational (non-audit) persistence.

Every method takes tenant_id as an explicit first argument. Tenant
filtering is a contract obligation of the repository, not something a
caller can forget to apply -- this mirrors
docs/ShieldEPC_Architecture_Spec_v1.md §9 (target architecture is Postgres
row-level security with tenant_id on every table). Baking tenant scoping
into the interface now means the eventual Postgres/RLS implementation is a
drop-in replacement for the SQLite implementation, not a redesign.

Nothing above the repository layer (services, API routes) should ever
import sqlite3 or a Postgres driver directly -- only repository
implementations do that.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Generic tenant-scoped repository contract. T is the entity type
    a concrete repository manages (e.g. Tenant, Project)."""

    @abstractmethod
    def get_by_id(self, tenant_id: str, entity_id: str) -> Optional[T]:
        """Return the entity if it exists and belongs to tenant_id, else None."""
        raise NotImplementedError

    @abstractmethod
    def list(self, tenant_id: str) -> list[T]:
        """Return all entities belonging to tenant_id."""
        raise NotImplementedError

    @abstractmethod
    def save(self, tenant_id: str, entity: T) -> T:
        """Insert or update entity, scoped to tenant_id. Returns the saved entity."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, tenant_id: str, entity_id: str) -> bool:
        """Delete entity if it belongs to tenant_id. Returns True if a row was deleted."""
        raise NotImplementedError
