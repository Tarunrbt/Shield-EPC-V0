"""
Envelope serialization round-trip tests for InvestigatorSignoff
(Phase 4C Step 2).
"""
from datetime import datetime, timezone

from app.envelope.schema import InvestigatorSignoff, EnvelopeContent


def test_investigator_signoff_json_round_trip_pending():
    obj = InvestigatorSignoff(status="pending")
    data = obj.model_dump(mode="json")
    restored = InvestigatorSignoff.model_validate(data)
    assert restored == obj


def test_investigator_signoff_json_round_trip_signed():
    ts = datetime.now(timezone.utc)
    obj = InvestigatorSignoff(
        status="signed",
        investigator_id="emp_123",
        signed_at=ts,
    )
    data = obj.model_dump(mode="json")
    restored = InvestigatorSignoff.model_validate(data)
    assert restored.status == obj.status
    assert restored.investigator_id == obj.investigator_id
    assert restored.signed_at == obj.signed_at


def test_investigator_signoff_json_round_trip_rejected():
    ts = datetime.now(timezone.utc)
    obj = InvestigatorSignoff(
        status="rejected",
        investigator_id="emp_789",
        signed_at=ts,
    )
    data = obj.model_dump(mode="json")
    restored = InvestigatorSignoff.model_validate(data)
    assert restored.status == obj.status
    assert restored.investigator_id == obj.investigator_id
    assert restored.signed_at == obj.signed_at


def test_investigator_signoff_within_envelope_content_round_trip():
    signoff = InvestigatorSignoff(
        status="rejected",
        investigator_id="emp_456",
        signed_at=datetime.now(timezone.utc),
    )
    content = EnvelopeContent(
        answer="test",
        confidence_score=1.0,
        confidence_basis="test basis",
        investigator_signoff=signoff,
    )
    data = content.model_dump(mode="json")
    restored = EnvelopeContent.model_validate(data)
    assert restored.investigator_signoff.status == "rejected"
    assert restored.investigator_signoff.investigator_id == "emp_456"
    assert restored.investigator_signoff.signed_at == signoff.signed_at


def test_envelope_content_with_pending_signoff_round_trip():
    content = EnvelopeContent(
        answer="test",
        confidence_score=0.5,
        confidence_basis="test basis",
        investigator_signoff=InvestigatorSignoff(status="pending"),
    )
    data = content.model_dump(mode="json")
    restored = EnvelopeContent.model_validate(data)
    assert restored.investigator_signoff.status == "pending"
    assert restored.investigator_signoff.investigator_id is None
    assert restored.investigator_signoff.signed_at is None


def test_envelope_content_without_signoff_round_trip():
    content = EnvelopeContent(
        answer="test",
        confidence_score=0.9,
        confidence_basis="test basis",
    )
    data = content.model_dump(mode="json")
    restored = EnvelopeContent.model_validate(data)
    assert restored.investigator_signoff is None
