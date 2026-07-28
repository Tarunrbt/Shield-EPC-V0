"""
Tenant HTTP endpoints.

Thin routing layer -- validates/maps the request and delegates to
TenantService (app/bootstrap.py singleton). Domain exceptions
(TenantNotFound, ValidationFailed) are not caught here; they propagate
to the global exception handler registered in main.py.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.bootstrap import tenant_service
from app.db.models import Tenant

router = APIRouter(prefix="/tenants", tags=["tenants"])


class CreateTenantRequest(BaseModel):
    name: str


class TenantResponse(BaseModel):
    tenant_id: str
    name: str
    status: str
    created_at: str

    @classmethod
    def from_entity(cls, tenant: Tenant) -> "TenantResponse":
        return cls(
            tenant_id=tenant.tenant_id,
            name=tenant.name,
            status=tenant.status,
            created_at=tenant.created_at,
        )


@router.post("", response_model=TenantResponse, status_code=201)
def create_tenant(payload: CreateTenantRequest) -> TenantResponse:
    tenant = tenant_service.create_tenant(payload.name)
    return TenantResponse.from_entity(tenant)


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: str) -> TenantResponse:
    tenant = tenant_service.get_tenant(tenant_id)
    return TenantResponse.from_entity(tenant)


@router.post("/{tenant_id}/deactivate", response_model=TenantResponse)
def deactivate_tenant(tenant_id: str) -> TenantResponse:
    tenant = tenant_service.deactivate_tenant(tenant_id)
    return TenantResponse.from_entity(tenant)
