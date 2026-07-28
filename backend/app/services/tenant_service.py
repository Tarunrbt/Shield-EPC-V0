"""
TenantService — domain logic for Tenant lifecycle.

Depends only on BaseRepository[Tenant] (the interface), never on
TenantRepository or sqlite3 directly. This keeps the service swappable
against any future repository implementation (Postgres/RLS, etc.).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.models import Tenant
from app.db.repositories.base import BaseRepository
from core.exceptions import TenantNotFound, ValidationFailed


class TenantService:
    def __init__(self, repository: BaseRepository[Tenant]):
        self._repo = repository

    def create_tenant(self, name: str) -> Tenant:
        if not name or not name.strip():
            raise ValidationFailed("Tenant name cannot be empty", field="name", value=name)

        tenant_id = str(uuid.uuid4())
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name.strip(),
            status="active",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return self._repo.save(tenant_id, tenant)

    def get_tenant(self, tenant_id: str) -> Tenant:
        tenant = self._repo.get_by_id(tenant_id, tenant_id)
        if tenant is None:
            raise TenantNotFound(
                f"Tenant not found: {tenant_id}",
                tenant_id=tenant_id,
            )
        return tenant

    def deactivate_tenant(self, tenant_id: str) -> Tenant:
        tenant = self.get_tenant(tenant_id)
        updated = Tenant(
            tenant_id=tenant.tenant_id,
            name=tenant.name,
            status="inactive",
            created_at=tenant.created_at,
        )
        return self._repo.save(tenant_id, updated)
