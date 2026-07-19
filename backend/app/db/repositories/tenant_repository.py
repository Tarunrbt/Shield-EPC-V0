"""
SQLite implementation of BaseRepository for Tenant entities.

Tenant is a special case for the tenant-scoped contract: a tenant's own
tenant_id *is* its entity_id (it scopes itself). get_by_id enforces
tenant_id == entity_id, so a mismatched pair returns None rather than
silently ignoring the tenant_id argument -- this keeps the contract
consistent with repositories where tenant_id is a genuine foreign key
(e.g. ProjectRepository), rather than special-casing Tenant's behavior.

Caller is responsible for generating tenant_id (e.g. uuid4 string) --
this repository only persists, it never generates identifiers. See
app/db/repositories/base.py for the abstract contract this implements.
"""

from __future__ import annotations

from typing import Optional

from app.db.database import connection_scope
from app.db.models import Tenant
from app.db.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    def __init__(self, db_path=None):
        self._db_path = db_path

    def _scope(self):
        return connection_scope(self._db_path) if self._db_path else connection_scope()

    def get_by_id(self, tenant_id: str, entity_id: str) -> Optional[Tenant]:
        if tenant_id != entity_id:
            return None
        with self._scope() as conn:
            row = conn.execute(
                "SELECT tenant_id, name, status, created_at FROM tenant "
                "WHERE tenant_id = ?",
                (entity_id,),
            ).fetchone()
        if row is None:
            return None
        return Tenant(
            tenant_id=row["tenant_id"],
            name=row["name"],
            status=row["status"],
            created_at=row["created_at"],
        )

    def list(self, tenant_id: str) -> list[Tenant]:
        # A tenant only ever "lists" itself under this contract -- there
        # is no parent scope above Tenant. Mirrors get_by_id's semantics.
        found = self.get_by_id(tenant_id, tenant_id)
        return [found] if found is not None else []

    def save(self, tenant_id: str, entity: Tenant) -> Tenant:
        if tenant_id != entity.tenant_id:
            raise ValueError(
                f"tenant_id argument ({tenant_id!r}) does not match "
                f"entity.tenant_id ({entity.tenant_id!r})"
            )
        with self._scope() as conn:
            conn.execute(
                """
                INSERT INTO tenant (tenant_id, name, status, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (tenant_id) DO UPDATE SET
                    name = excluded.name,
                    status = excluded.status,
                    created_at = excluded.created_at
                """,
                (entity.tenant_id, entity.name, entity.status, entity.created_at),
            )
        return entity

    def delete(self, tenant_id: str, entity_id: str) -> bool:
        if tenant_id != entity_id:
            return False
        with self._scope() as conn:
            cursor = conn.execute(
                "DELETE FROM tenant WHERE tenant_id = ?", (entity_id,)
            )
        return cursor.rowcount > 0
