"""
SQLite implementation of BaseRepository for Project entities.

Unlike TenantRepository, tenant_id here is a genuine foreign key -- every
query is filtered by tenant_id at the SQL level (WHERE tenant_id = ?),
which is the actual cross-tenant isolation mechanism until the eventual
Postgres + row-level security migration (spec S9). A project row existing
in the DB is not sufficient for get_by_id/delete to return it -- it must
also belong to the tenant_id passed in.

Caller is responsible for generating project_id. See
app/db/repositories/base.py for the abstract contract this implements.
"""

from __future__ import annotations

from typing import Optional

from app.db.database import connection_scope
from app.db.models import Project
from app.db.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db_path=None):
        self._db_path = db_path

    def _scope(self):
        return connection_scope(self._db_path) if self._db_path else connection_scope()

    def get_by_id(self, tenant_id: str, entity_id: str) -> Optional[Project]:
        with self._scope() as conn:
            row = conn.execute(
                "SELECT project_id, tenant_id, name, created_at FROM project "
                "WHERE project_id = ? AND tenant_id = ?",
                (entity_id, tenant_id),
            ).fetchone()
        if row is None:
            return None
        return Project(
            project_id=row["project_id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            created_at=row["created_at"],
        )

    def list(self, tenant_id: str) -> list[Project]:
        with self._scope() as conn:
            rows = conn.execute(
                "SELECT project_id, tenant_id, name, created_at FROM project "
                "WHERE tenant_id = ? ORDER BY created_at",
                (tenant_id,),
            ).fetchall()
        return [
            Project(
                project_id=r["project_id"],
                tenant_id=r["tenant_id"],
                name=r["name"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def save(self, tenant_id: str, entity: Project) -> Project:
        if tenant_id != entity.tenant_id:
            raise ValueError(
                f"tenant_id argument ({tenant_id!r}) does not match "
                f"entity.tenant_id ({entity.tenant_id!r})"
            )
        with self._scope() as conn:
            conn.execute(
                """
                INSERT INTO project (project_id, tenant_id, name, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (project_id) DO UPDATE SET
                    name = excluded.name,
                    created_at = excluded.created_at
                WHERE project.tenant_id = excluded.tenant_id
                """,
                (entity.project_id, entity.tenant_id, entity.name, entity.created_at),
            )
        return entity

    def delete(self, tenant_id: str, entity_id: str) -> bool:
        with self._scope() as conn:
            cursor = conn.execute(
                "DELETE FROM project WHERE project_id = ? AND tenant_id = ?",
                (entity_id, tenant_id),
            )
        return cursor.rowcount > 0
