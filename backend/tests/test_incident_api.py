"""
Incident Investigation API integration tests -- real HTTP calls via
TestClient, following the same pattern as tests/test_tenant_api.py:
imports the shared `client` from test_api.py, which owns DB_PATH /
AUDIT_LOG_PATH isolation.
"""

from __future__ import annotations

from test_api import client


def _valid_payload() -> dict:
    return {
        "incident_description": "Worker slipped",
        "five_whys": ["1", "2", "3"],
        "fishbone_causes": {
            "people_factors": [],
            "process": [],
            "equipment": [],
            "materials": [],
            "environment": [],
        },
        "bowtie_top_event": "Slip",
        "bowtie_threats": ["Wet floor"],
        "bowtie_consequences": ["Minor injury"],
        "preventive_barriers": ["Inspection"],
        "mitigative_barriers": ["First aid"],
        "tenant_id": "tenant_test",
        "user_id": "user_test",
    }


def test_incident_investigation_returns_200():
    payload = _valid_payload()

    response = client.post("/incident-investigation", json=payload)

    assert response.status_code == 200

    body = response.json()

    assert body["agent"] == "incident_investigation_agent"
    assert body["human_review_required"] is True
    assert body["human_review_reason"] == "statutory_requirement"

    assert body["content"]["five_whys"] == ["1", "2", "3"]
    assert body["content"]["fishbone_causes"] == payload["fishbone_causes"]
    assert body["content"]["bowtie"]["top_event"] == "Slip"
    assert body["content"]["investigator_signoff"]["signed_off"] is False

    assert body["audit_trail_id"]


def test_incident_investigation_missing_required_field_returns_422():
    payload = _valid_payload()
    del payload["incident_description"]

    response = client.post("/incident-investigation", json=payload)

    assert response.status_code == 422
