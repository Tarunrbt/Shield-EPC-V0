"""
Phase 4C Step 3 -- API contract verification for InvestigatorSignoff.

Confirms the /incident-investigation endpoint response matches the new
investigator_id/status/signed_at schema, and that the old
signed_off/investigator_name/signoff_date fields are gone from both
the live response and the generated OpenAPI schema.
"""

from __future__ import annotations

import json

from test_api import client
from tests.test_incident_api import _valid_payload

OLD_FIELD_NAMES = {"signed_off", "investigator_name", "signoff_date"}


def test_response_investigator_signoff_has_new_fields():
    payload = _valid_payload()

    response = client.post("/incident-investigation", json=payload)
    assert response.status_code == 200

    signoff = response.json()["content"]["investigator_signoff"]

    assert set(signoff.keys()) == {"investigator_id", "status", "signed_at"}
    assert signoff["status"] == "pending"
    assert signoff["investigator_id"] is None
    assert signoff["signed_at"] is None


def test_response_body_contains_no_old_field_names():
    payload = _valid_payload()

    response = client.post("/incident-investigation", json=payload)
    assert response.status_code == 200

    raw_body = json.dumps(response.json())

    for old_field in OLD_FIELD_NAMES:
        assert old_field not in raw_body, (
            f"stale field '{old_field}' found in API response body"
        )


def test_openapi_schema_reflects_new_investigator_signoff_shape():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    schema_text = json.dumps(schema)

    assert "investigator_id" in schema_text
    assert '"status"' in schema_text or "'status'" in schema_text

    for old_field in OLD_FIELD_NAMES:
        assert old_field not in schema_text, (
            f"stale field '{old_field}' found in OpenAPI schema"
        )
