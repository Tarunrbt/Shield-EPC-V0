from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.bootstrap import orchestrator
from app.envelope.schema import ResponseEnvelope

router = APIRouter()


class TrainingRecordPayload(BaseModel):
    competency_name: str
    completed: bool
    completion_date: str | None = None
    expiry_date: str | None = None
    issuing_body: str | None = None


class TrainingCompetencyRequest(BaseModel):
    role_or_task: str
    assessment_date: str
    required_competencies: list[str]
    training_records: list[TrainingRecordPayload]
    tenant_id: str
    user_id: str | None = None


@router.post("/training-competency", response_model=ResponseEnvelope)
def training_competency(
    payload: TrainingCompetencyRequest,
) -> ResponseEnvelope:
    request = {
        "role_or_task": payload.role_or_task,
        "assessment_date": payload.assessment_date,
        "required_competencies": payload.required_competencies,
        "training_records": [
            record.model_dump() for record in payload.training_records
        ],
    }
    return orchestrator.handle(
        operation_type="training_competency",
        request=request,
        tenant_id=payload.tenant_id,
        user_id=payload.user_id,
    )
