import os
import sys
import tempfile
from pathlib import Path

_temp_dir = Path(tempfile.mkdtemp(prefix="shield_epc_api_test_"))
os.environ["AUDIT_LOG_PATH"] = str(_temp_dir / "audit_log.jsonl")
os.environ["DB_PATH"] = str(_temp_dir / "shield_epc.db")

from fastapi.testclient import TestClient

from app.main import app
from app.bootstrap import audit_log

client = TestClient(app)


def check(condition: bool, message: str) -> None:
    if not condition:
        print(f"FAIL: {message}")
        sys.exit(1)
    print(f"OK:   {message}")


def test_health() -> None:
    response = client.get("/health")
    check(response.status_code == 200, "GET /health returns 200")
    check(response.json() == {"status": "ok"}, "GET /health body is correct")


def test_root() -> None:
    response = client.get("/")
    check(response.status_code == 200, "GET / returns 200")
    check(response.json() == {"status": "ok"}, "GET / body is correct")


def _generate_document(client) -> dict:
    """
    POSTs to /generate and runs all response checks. Shared by the
    pytest test_generate() and by main()'s standalone script path,
    which needs the envelope dict to pass into test_audit_log_entry().
    """
    payload = {
        "template_id": "jsa_draft",
        "fields": {
            "task_description": "Excavation near buried services",
            "location": "Zone 4",
            "performed_by": "Test User",
            "date": "2026-07-14",
        },
        "tenant_id": "tenant_test_001",
        "user_id": "user_test_001",
    }
    response = client.post("/generate", json=payload)
    check(response.status_code == 200, "POST /generate returns 200")

    body = response.json()
    check(bool(body["content"]["answer"]), "response content.answer is non-empty")
    check(
        body["human_review_required"] is True,
        "human_review_required is True",
    )
    check(
        len(body["source_of_reasoning"]) == 1
        and body["source_of_reasoning"][0]["type"] == "structured_input",
        "source_of_reasoning cites structured_input",
    )
    check(bool(body["audit_trail_id"]), "audit_trail_id is present")
    return body


def test_generate() -> None:
    _generate_document(client)


def test_audit_log_entry(envelope: dict) -> None:
    entries = audit_log.read_all()
    check(len(entries) == 1, "exactly one audit log entry exists")
    check(
        entries[0]["entry_id"] == envelope["audit_trail_id"],
        "audit entry_id matches envelope audit_trail_id",
    )
    check(
        entries[0]["payload"]["outcome"] == "success",
        "audit outcome is success",
    )
    check(
        entries[0]["payload"]["verification"]["verification_status"] == "verified",
        "audit verification_status is verified",
    )


def main() -> None:
    test_health()
    test_root()
    envelope = _generate_document(client)
    test_audit_log_entry(envelope)
    print("\n✅ Phase 2 API integration tests PASSED")


if __name__ == "__main__":
    main()
