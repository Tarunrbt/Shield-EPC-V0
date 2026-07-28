"""
Tenant API integration tests — real HTTP calls via TestClient, hitting
the actual SQLite DB through the full stack: API -> TenantService ->
TenantRepository -> SQLite. DB_PATH/AUDIT_LOG_PATH isolation is handled
by test_api.py, which conftest.py's fixtures rely on already being
imported (same pattern as tests/test_tenant_repository.py's use of a
temp DB, but here through the HTTP layer instead of the repository
directly).
"""

from __future__ import annotations

from test_api import client


def test_create_tenant_returns_201():
    response = client.post("/tenants", json={"name": "Acme Corp"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Acme Corp"
    assert body["status"] == "active"
    assert body["tenant_id"]


def test_create_tenant_empty_name_returns_400():
    response = client.post("/tenants", json={"name": "   "})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_get_tenant_returns_200():
    created = client.post("/tenants", json={"name": "Beta LLC"}).json()

    response = client.get(f"/tenants/{created['tenant_id']}")

    assert response.status_code == 200
    assert response.json()["tenant_id"] == created["tenant_id"]
    assert response.json()["name"] == "Beta LLC"


def test_get_tenant_missing_returns_404():
    response = client.get("/tenants/nonexistent_tenant_id")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TENANT_NOT_FOUND"


def test_deactivate_tenant_sets_status_inactive():
    created = client.post("/tenants", json={"name": "Gamma Inc"}).json()

    response = client.post(f"/tenants/{created['tenant_id']}/deactivate")

    assert response.status_code == 200
    assert response.json()["status"] == "inactive"


def test_deactivate_tenant_missing_returns_404():
    response = client.post("/tenants/nonexistent_tenant_id/deactivate")

    assert response.status_code == 404
