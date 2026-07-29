from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.bootstrap import orchestrator
from app.envelope.schema import ResponseEnvelope

router = APIRouter()


class IncidentInvestigationRequest(BaseModel):
    incident_description: str
    five_whys: list[str]
    fishbone_causes: dict[str, list[str]]
    bowtie_top_event: str
    bowtie_threats: list[str]
    bowtie_consequences: list[str]
    preventive_barriers: list[str]
    mitigative_barriers: list[str]
    tenant_id: str
    user_id: str | None = None


@router.post("/incident-investigation", response_model=ResponseEnvelope)
def incident_investigation(
    payload: IncidentInvestigationRequest,
) -> ResponseEnvelope:
    request = {
        "incident_description": payload.incident_description,
        "five_whys": payload.five_whys,
        "fishbone_causes": payload.fishbone_causes,
        "bowtie_top_event": payload.bowtie_top_event,
        "bowtie_threats": payload.bowtie_threats,
        "bowtie_consequences": payload.bowtie_consequences,
        "preventive_barriers": payload.preventive_barriers,
        "mitigative_barriers": payload.mitigative_barriers,
    }
    return orchestrator.handle(
        operation_type="incident_investigation",
        request=request,
        tenant_id=payload.tenant_id,
        user_id=payload.user_id,
    )
