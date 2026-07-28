"""
TenantService tests — uses an in-memory fake repository implementing
BaseRepository[Tenant], not the real SQLite TenantRepository.
"""

from __future__ import annotations

import pytest

from app.db.models import Tenant
from app.db.repositories.base import BaseRepository
from app.services.tenant_service import TenantService
from core.exceptions import TenantNotFound, ValidationFailed


class FakeTenantRepository(BaseRepository[Tenant]):
    def __init__(self):
        self._store: dict[str, Tenant] = {}

    def get_by_id(self, tenant_id: str, entity_id: str):
        if tenant_id != entity_id:
            return None
        return self._store.get(entity_id)

    def list(self, tenant_id: str):
        found = self._store.get(tenant_id)
        return [found] if found is not None else []

    def save(self, tenant_id: str, entity: Tenant) -> Tenant:
        self._store[tenant_id] = entity
        return entity

    def delete(self, tenant_id: str, entity_id: str) -> bool:
        if tenant_id != entity_id or entity_id not in self._store:
            return False
        del self._store[entity_id]
        return True


@pytest.fixture
def repo():
    return FakeTenantRepository()


@pytest.fixture
def service(repo):
    return TenantService(repo)


def test_create_tenant_persists_and_returns(service):
    tenant = service.create_tenant("Acme Corp")
    assert tenant.name == "Acme Corp"
    assert tenant.status == "active"
    assert tenant.tenant_id


def test_create_tenant_rejects_empty_name(service):
    with pytest.raises(ValidationFailed):
        service.create_tenant("   ")


def test_get_tenant_returns_saved_tenant(service):
    created = service.create_tenant("Acme Corp")
    fetched = service.get_tenant(created.tenant_id)
    assert fetched.tenant_id == created.tenant_id
    assert fetched.name == "Acme Corp"


def test_get_tenant_raises_when_missing(service, tenant_id):
    with pytest.raises(TenantNotFound):
        service.get_tenant(tenant_id)


def test_deactivate_tenant_sets_status_inactive(service):
    created = service.create_tenant("Acme Corp")
    deactivated = service.deactivate_tenant(created.tenant_id)
    assert deactivated.status == "inactive"
    assert deactivated.tenant_id == created.tenant_id
    assert deactivated.name == created.name
    assert deactivated.created_at == created.created_at


def test_deactivate_tenant_raises_when_missing(service, tenant_id):
    with pytest.raises(TenantNotFound):
        service.deactivate_tenant(tenant_id)
