"""
ProjectService — domain logic for Project lifecycle, scoped to a tenant.

Depends only on BaseRepository[Project]. Duplicate-name checks and
NotFound handling live here, not in the repository (repository only
knows persistence, not domain rules).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.models import Project
from app.db.repositories.base import BaseRepository
from core.exceptions import DocumentNotFound, ValidationFailed


class ProjectService:
    def __init__(self, repository: BaseRepository[Project]):
        self._repo = repository

    def create_project(self, tenant_id: str, name: str) -> Project:
        if not name or not name.strip():
            raise ValidationFailed("Project name cannot be empty", field="name", value=name)

        existing = self._repo.list(tenant_id)
        if any(p.name.strip().lower() == name.strip().lower() for p in existing):
            raise ValidationFailed(
                f"Project with name '{name}' already exists for this tenant",
                field="name",
                value=name,
                metadata={"tenant_id": tenant_id},
            )

        project_id = str(uuid.uuid4())
        project = Project(
            project_id=project_id,
            tenant_id=tenant_id,
            name=name.strip(),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return self._repo.save(tenant_id, project)

    def get_project(self, tenant_id: str, project_id: str) -> Project:
        project = self._repo.get_by_id(tenant_id, project_id)
        if project is None:
            # TODO(ADR): Replace DocumentNotFound with ProjectNotFound
            # once the core exception hierarchy gains a project-specific error.
            raise DocumentNotFound(
                f"Project not found: {project_id}",
                document_id=project_id,
                tenant_id=tenant_id,
            )
        return project

    def list_projects(self, tenant_id: str) -> list[Project]:
        return self._repo.list(tenant_id)

    def delete_project(self, tenant_id: str, project_id: str) -> None:
        self.get_project(tenant_id, project_id)
        self._repo.delete(tenant_id, project_id)
