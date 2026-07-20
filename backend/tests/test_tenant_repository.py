"""
Unit tests for TenantRepository (Persistence Phase 3A).

Each test gets its own tmp_path-scoped SQLite file -- never touches
data/shield_epc.db. Verifies BaseRepository contract compliance plus
Tenant-specific semantics (tenant_id == entity_id enforcement).
"""

from datetime import datetime, timezone
import sqlite3

import pytest

from app.db.database import init_schema
from app.db.models import Tenant
from app.db.models import Project
from app.db.repositories.tenant_repository import TenantRepository
from app.db.repositories.project_repository import ProjectRepository


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test_tenant.db"
    init_schema(path)
    return path


@pytest.fixture
def repo(db_path):
    return TenantRepository(db_path)


def _make_tenant(tenant_id: str, name: str = "Acme EPC") -> Tenant:
    return Tenant(
        tenant_id=tenant_id,
        name=name,
        status="active",
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def test_save_and_get_tenant(repo, tenant_id):
    tenant = _make_tenant(tenant_id)

    saved = repo.save(tenant_id, tenant)
    assert saved == tenant

    fetched = repo.get_by_id(tenant_id, tenant_id)
    assert fetched == tenant


def test_get_missing_tenant(repo, tenant_id):
    assert repo.get_by_id(tenant_id, tenant_id) is None


def test_get_by_id_mismatched_ids_returns_none(repo, tenant_id):
    tenant = _make_tenant(tenant_id)
    repo.save(tenant_id, tenant)

    # tenant_id != entity_id must return None, even though the row exists
    assert repo.get_by_id("some_other_tenant", tenant_id) is None


def test_list_tenants(repo, tenant_id):
    assert repo.list(tenant_id) == []

    tenant = _make_tenant(tenant_id)
    repo.save(tenant_id, tenant)

    assert repo.list(tenant_id) == [tenant]


def test_delete_tenant(repo, tenant_id):
    tenant = _make_tenant(tenant_id)
    repo.save(tenant_id, tenant)

    deleted = repo.delete(tenant_id, tenant_id)
    assert deleted is True
    assert repo.get_by_id(tenant_id, tenant_id) is None


def test_delete_missing_tenant(repo, tenant_id):
    assert repo.delete(tenant_id, tenant_id) is False


def test_save_updates_existing_tenant(repo, tenant_id):
    original = _make_tenant(tenant_id, name="Acme EPC")
    repo.save(tenant_id, original)

    updated = _make_tenant(tenant_id, name="Acme EPC Renamed")
    repo.save(tenant_id, updated)

    fetched = repo.get_by_id(tenant_id, tenant_id)
    assert fetched.name == "Acme EPC Renamed"
    # confirm it's an update, not a duplicate row
    assert len(repo.list(tenant_id)) == 1


def test_save_rejects_mismatched_tenant_id(repo, tenant_id):
    tenant = _make_tenant(tenant_id)
    with pytest.raises(ValueError):
        repo.save("different_tenant", tenant)




def test_delete_tenant_with_existing_project_raises_integrity_error(
    repo, db_path, tenant_id
):
    tenant = _make_tenant(tenant_id)
    repo.save(tenant_id, tenant)

    project_repo = ProjectRepository(db_path)
    project = Project(
        project_id="proj_1",
        tenant_id=tenant_id,
        name="Test Project",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    project_repo.save(tenant_id, project)

    with pytest.raises(sqlite3.IntegrityError):
        repo.delete(tenant_id, tenant_id)

    # tenant row must remain untouched since the delete was rejected
    assert repo.get_by_id(tenant_id, tenant_id) is not None
