from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, model_validator

from app.bootstrap import orchestrator
from app.envelope.schema import ResponseEnvelope

OperationType = Literal[
    "document_generation",
    "risk_assessment",
    "ptw_jsa",
]

router = APIRouter()


class GenerateRequest(BaseModel):
    template_id: str
    fields: dict[str, Any]
    tenant_id: str
    user_id: str | None = None
    operation_type: OperationType = "document_generation"

    @model_validator(mode="after")
    def validate_document_fields(self):
        if self.operation_type == "document_generation":
            invalid = [
                key
                for key, value in self.fields.items()
                if not isinstance(value, str)
            ]

            if invalid:
                raise ValueError(
                    f"Document fields must be strings: {invalid}"
                )

        return self


@router.post("/generate", response_model=ResponseEnvelope)
def generate(payload: GenerateRequest) -> ResponseEnvelope:
    request = {
        **payload.fields,
        "template_id": payload.template_id,
        "fields": payload.fields,
    }

    return orchestrator.handle(
        operation_type=payload.operation_type,
        request=request,
        tenant_id=payload.tenant_id,
        user_id=payload.user_id,
    )
