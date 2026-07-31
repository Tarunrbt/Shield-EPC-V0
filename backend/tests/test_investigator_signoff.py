"""
Negative-path and positive-path validation tests for InvestigatorSignoff
(Phase 4B contract lock).
"""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.envelope.schema import InvestigatorSignoff


def test_pending_with_signed_at_raises():
    with pytest.raises(ValidationError):
        InvestigatorSignoff(
            status="pending",
            investigator_id=None,
            signed_at=datetime.now(timezone.utc),
        )


def test_signed_with_signed_at_none_raises():
    with pytest.raises(ValidationError):
        InvestigatorSignoff(
            status="signed",
            investigator_id="emp_123",
            signed_at=None,
        )


def test_signed_with_investigator_id_none_raises():
    with pytest.raises(ValidationError):
        InvestigatorSignoff(
            status="signed",
            investigator_id=None,
            signed_at=datetime.now(timezone.utc),
        )


def test_rejected_with_investigator_id_none_raises():
    with pytest.raises(ValidationError):
        InvestigatorSignoff(
            status="rejected",
            investigator_id=None,
            signed_at=datetime.now(timezone.utc),
        )


def test_signed_at_timezone_naive_raises():
    with pytest.raises(ValidationError):
        InvestigatorSignoff(
            status="signed",
            investigator_id="emp_123",
            signed_at=datetime.now(),  # naive, no tzinfo
        )


def test_valid_pending_object():
    obj = InvestigatorSignoff(status="pending")
    assert obj.status == "pending"
    assert obj.investigator_id is None
    assert obj.signed_at is None


def test_valid_signed_object():
    ts = datetime.now(timezone.utc)
    obj = InvestigatorSignoff(
        status="signed",
        investigator_id="emp_123",
        signed_at=ts,
    )
    assert obj.status == "signed"
    assert obj.investigator_id == "emp_123"
    assert obj.signed_at == ts


def test_valid_rejected_object():
    ts = datetime.now(timezone.utc)
    obj = InvestigatorSignoff(
        status="rejected",
        investigator_id="emp_456",
        signed_at=ts,
    )
    assert obj.status == "rejected"
    assert obj.investigator_id == "emp_456"
