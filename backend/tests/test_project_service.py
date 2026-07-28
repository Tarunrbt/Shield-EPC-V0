"""
ProjectService tests — uses an in-memory fake repository implementing
BaseRepository[Project], not the real SQLite ProjectRepository.
"""

from __future__ import annotations

import pytest

from app.db.models import Project
from app.db.repositories.base import BaseRepository
from app.services.project_service import ProjectService
from core.exceptions import DocumentNotFound, ValidationFailed


class FakeProjectRepository(BaseRepository[Project]):
    def __init__(self):
        self._store: dict[str, Project] = {}

    def get_by_id(self, tenant_id: str, entity_id: str):
        project = self._store.get(entity_id)
        if project is None or project.tenant_id != tenant_id:
            return None
        return project

    def list(self, tenant_id: str):
        return [p for p in self._store.values() if p.tenant_id == tenant_id]

    def save(self, tenant_id: str, entity: Project) -> Project:
        self._store[entity.project_id] = entity
        return entity

    def delete(self, tenant_id: str, entity_id: str) -> bool:
        project = self._store.get(entity_id)
        if project is None or project.tenant_id != tenant_id:
            return False
        del self._store[entity_id]
        return True


@pytest.fixture
def repo():
    return FakeProjectRepository()


@pytest.fixture
def service(repo):
    return ProjectService(repo)


def test_create_project_persists_and_returns(service, tenant_id):
    project = service.create_project(tenant_id, "Site Survey Alpha")
    assert project.name == "Site Survey Alpha"
    assert project.tenant_id == tenant_id
    assert project.project_id


def test_create_project_rejects_empty_name(service, tenant_id):
    with pytest.raises(ValidationFailed):
        service.create_project(tenant_id, "  ")


def test_create_project_rejects_duplicate_name_same_tenant(service, tenant_id):
    service.create_project(tenant_id, "Site Survey Alpha")
    with pytest.raises(ValidationFailed):
        service.create_project(tenant_id, "site survey alpha")


def test_create_project_allows_same_name_different_tenant(service, tenant_id):
    service.create_project(tenant_id, "Site Survey Alpha")
    other = service.create_project("tenant_other_001", "Site Survey Alpha")
    assert other.name == "Site Survey Alpha"


def test_get_project_returns_saved_project(service, tenant_id):
    created = service.create_project(tenant_id, "Site Survey Alpha")
    fetched = service.get_project(tenant_id, created.project_id)
    assert fetched.project_id == created.project_id


def test_get_project_raises_when_missing(service, tenant_id):
    with pytest.raises(DocumentNotFound):
        service.get_project(tenant_id, "nonexistent_id")


def test_get_project_raises_when_wrong_tenant(service, tenant_id):
    created = service.create_project(tenant_id, "Site Survey Alpha")
    with pytest.raises(DocumentNotFound):
        service.get_project("tenant_other_001", created.project_id)


def test_list_projects_scoped_to_tenant(service, tenant_id):
    service.create_project(tenant_id, "Project A")
    service.create_project(tenant_id, "Project B")
    service.create_project("tenant_other_001", "Project C")
    projects = service.list_projects(tenant_id)
    assert {p.name for p in projects} == {"Project A", "Project B"}


def test_delete_project_removes_it(service, tenant_id):
    created = service.create_project(tenant_id, "Site Survey Alpha")
    service.delete_project(tenant_id, created.project_id)
    with pytest.raises(DocumentNotFound):
        service.get_project(tenant_id, created.project_id)


def test_delete_project_raises_when_missing(service, tenant_id):
    with pytest.raises(DocumentNotFound):
        service.delete_project(tenant_id, "nonexistent_id")
