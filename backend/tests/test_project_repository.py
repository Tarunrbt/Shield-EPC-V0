"""
Unit tests for ProjectRepository (Persistence Phase 3B).

Focus areas beyond the TenantRepository pattern: cross-tenant isolation
(a project must not be visible/mutable via a different tenant_id) and
foreign key enforcement against the tenant table.
"""

from datetime import datetime, timezone

import pytest
import sqlite3

from app.db.database import init_schema, connection_scope
from app.db.models import Project, Tenant
from app.db.repositories.project_repository import ProjectRepository
from app.db.repositories.tenant_repository import TenantRepository


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test_project.db"
    init_schema(path)
    return path


@pytest.fixture
def repo(db_path):
    return ProjectRepository(db_path)


@pytest.fixture
def seeded_tenant(db_path, tenant_id):
    """Most project tests need a real tenant row for the FK to satisfy."""
    tenant = Tenant(
        tenant_id=tenant_id,
        name="Acme EPC",
        status="active",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    TenantRepository(db_path).save(tenant_id, tenant)
    return tenant


def _make_project(project_id: str, tenant_id: str, name: str = "Hazira Site") -> Project:
    return Project(
        project_id=project_id,
        tenant_id=tenant_id,
        name=name,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def test_save_and_get_project(repo, seeded_tenant, tenant_id):
    project = _make_project("proj_001", tenant_id)
    repo.save(tenant_id, project)

    fetched = repo.get_by_id(tenant_id, "proj_001")
    assert fetched == project


def test_get_missing_project(repo, seeded_tenant, tenant_id):
    assert repo.get_by_id(tenant_id, "does_not_exist") is None


def test_cross_tenant_get_returns_none(repo, seeded_tenant, tenant_id):
    project = _make_project("proj_001", tenant_id)
    repo.save(tenant_id, project)

    # same project_id, wrong tenant_id -- must not be visible
    assert repo.get_by_id("some_other_tenant", "proj_001") is None


def test_list_only_returns_own_tenant_projects(repo, db_path, tenant_id):
    other_tenant_id = "tenant_test_002"
    now = datetime.now(timezone.utc).isoformat()
    TenantRepository(db_path).save(
        tenant_id, Tenant(tenant_id, "Acme EPC", "active", now)
    )
    TenantRepository(db_path).save(
        other_tenant_id, Tenant(other_tenant_id, "Other Co", "active", now)
    )

    repo.save(tenant_id, _make_project("proj_a", tenant_id))
    repo.save(other_tenant_id, _make_project("proj_b", other_tenant_id))

    result = repo.list(tenant_id)
    assert [p.project_id for p in result] == ["proj_a"]


def test_delete_project(repo, seeded_tenant, tenant_id):
    repo.save(tenant_id, _make_project("proj_001", tenant_id))
    assert repo.delete(tenant_id, "proj_001") is True
    assert repo.get_by_id(tenant_id, "proj_001") is None


def test_delete_missing_project(repo, seeded_tenant, tenant_id):
    assert repo.delete(tenant_id, "proj_001") is False


def test_cross_tenant_delete_does_not_remove_project(repo, seeded_tenant, tenant_id):
    repo.save(tenant_id, _make_project("proj_001", tenant_id))

    deleted = repo.delete("some_other_tenant", "proj_001")
    assert deleted is False
    # project must still exist, untouched
    assert repo.get_by_id(tenant_id, "proj_001") is not None


def test_save_updates_existing_project(repo, seeded_tenant, tenant_id):
    repo.save(tenant_id, _make_project("proj_001", tenant_id, name="Old Name"))
    repo.save(tenant_id, _make_project("proj_001", tenant_id, name="New Name"))

    fetched = repo.get_by_id(tenant_id, "proj_001")
    assert fetched.name == "New Name"
    assert len(repo.list(tenant_id)) == 1


def test_save_rejects_mismatched_tenant_id(repo, seeded_tenant, tenant_id):
    project = _make_project("proj_001", tenant_id)
    with pytest.raises(ValueError):
        repo.save("different_tenant", project)


def test_foreign_key_violation_rejected(repo, db_path, tenant_id):
    """No tenant row exists for tenant_id -- the FK constraint (enabled
    via PRAGMA foreign_keys = ON in database.py) must reject the insert."""
    project = _make_project("proj_001", tenant_id)
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(tenant_id, project)
