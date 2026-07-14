from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.bootstrap import document_generator_agent, orchestrator
from app.envelope.schema import ResponseEnvelope

router = APIRouter()


class GenerateRequest(BaseModel):
    template_id: str
    fields: dict[str, str]
    tenant_id: str
    user_id: str | None = None


@router.post("/generate", response_model=ResponseEnvelope)
def generate(payload: GenerateRequest) -> ResponseEnvelope:
    request = {
        "template_id": payload.template_id,
        "fields": payload.fields,
    }
    return orchestrator.handle(
        agent=document_generator_agent,
        request=request,
        tenant_id=payload.tenant_id,
        user_id=payload.user_id,
    )
