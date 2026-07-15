from __future__ import annotations

from typing import Literal
from fastapi import APIRouter
from pydantic import BaseModel

from app.bootstrap import orchestrator
from app.envelope.schema import ResponseEnvelope

OperationType = Literal["document_generation", "risk_assessment", "ptw_jsa"]

router = APIRouter()


class GenerateRequest(BaseModel):
    template_id: str
    fields: dict[str, str]
    tenant_id: str
    user_id: str | None = None
    operation_type: OperationType = "document_generation"


@router.post("/generate", response_model=ResponseEnvelope)
def generate(payload: GenerateRequest) -> ResponseEnvelope:
    request = {
        "template_id": payload.template_id,
        "fields": payload.fields,
    }
    return orchestrator.handle(
        operation_type=payload.operation_type,
        request=request,
        tenant_id=payload.tenant_id,
        user_id=payload.user_id,
    )
