"""
Project API integration tests — real HTTP calls via TestClient, hitting
the actual SQLite DB through the full stack: API -> ProjectService ->
ProjectRepository -> SQLite.
"""

from __future__ import annotations

from test_api import client


def _new_tenant(name: str = "Project Test Tenant") -> str:
    return client.post("/tenants", json={"name": name}).json()["tenant_id"]


def test_create_project_returns_201():
    tenant_id = _new_tenant()

    response = client.post(
        "/projects", json={"tenant_id": tenant_id, "name": "Site Survey Alpha"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Site Survey Alpha"
    assert body["tenant_id"] == tenant_id
    assert body["project_id"]


def test_create_project_empty_name_returns_400():
    tenant_id = _new_tenant()

    response = client.post("/projects", json={"tenant_id": tenant_id, "name": "  "})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_create_project_duplicate_name_returns_400():
    tenant_id = _new_tenant()
    client.post("/projects", json={"tenant_id": tenant_id, "name": "Dup Project"})

    response = client.post(
        "/projects", json={"tenant_id": tenant_id, "name": "Dup Project"}
    )

    assert response.status_code == 400


def test_get_project_returns_200():
    tenant_id = _new_tenant()
    created = client.post(
        "/projects", json={"tenant_id": tenant_id, "name": "Site Survey Beta"}
    ).json()

    response = client.get(
        f"/projects/{created['project_id']}", params={"tenant_id": tenant_id}
    )

    assert response.status_code == 200
    assert response.json()["project_id"] == created["project_id"]


def test_get_project_missing_returns_404():
    tenant_id = _new_tenant()

    response = client.get(
        "/projects/nonexistent_project_id", params={"tenant_id": tenant_id}
    )

    assert response.status_code == 404


def test_get_project_wrong_tenant_returns_404():
    tenant_a = _new_tenant("Tenant A")
    tenant_b = _new_tenant("Tenant B")
    created = client.post(
        "/projects", json={"tenant_id": tenant_a, "name": "Isolated Project"}
    ).json()

    response = client.get(
        f"/projects/{created['project_id']}", params={"tenant_id": tenant_b}
    )

    assert response.status_code == 404


def test_list_projects_scoped_to_tenant():
    tenant_id = _new_tenant()
    client.post("/projects", json={"tenant_id": tenant_id, "name": "P1"})
    client.post("/projects", json={"tenant_id": tenant_id, "name": "P2"})

    response = client.get("/projects", params={"tenant_id": tenant_id})

    assert response.status_code == 200
    names = {p["name"] for p in response.json()}
    assert {"P1", "P2"}.issubset(names)


def test_delete_project_removes_it():
    tenant_id = _new_tenant()
    created = client.post(
        "/projects", json={"tenant_id": tenant_id, "name": "To Delete"}
    ).json()

    delete_response = client.delete(
        f"/projects/{created['project_id']}", params={"tenant_id": tenant_id}
    )
    assert delete_response.status_code == 204

    get_response = client.get(
        f"/projects/{created['project_id']}", params={"tenant_id": tenant_id}
    )
    assert get_response.status_code == 404


def test_delete_project_missing_returns_404():
    tenant_id = _new_tenant()

    response = client.delete(
        "/projects/nonexistent_project_id", params={"tenant_id": tenant_id}
    )

    assert response.status_code == 404
