"""
Project HTTP endpoints.

Thin routing layer -- validates/maps the request and delegates to
ProjectService (app/bootstrap.py singleton). Domain exceptions
(DocumentNotFound, ValidationFailed) are not caught here; they
propagate to the global exception handler registered in main.py.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.bootstrap import project_service
from app.db.models import Project

router = APIRouter(prefix="/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    tenant_id: str
    name: str


class ProjectResponse(BaseModel):
    project_id: str
    tenant_id: str
    name: str
    created_at: str

    @classmethod
    def from_entity(cls, project: Project) -> "ProjectResponse":
        return cls(
            project_id=project.project_id,
            tenant_id=project.tenant_id,
            name=project.name,
            created_at=project.created_at,
        )


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(payload: CreateProjectRequest) -> ProjectResponse:
    project = project_service.create_project(payload.tenant_id, payload.name)
    return ProjectResponse.from_entity(project)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, tenant_id: str) -> ProjectResponse:
    project = project_service.get_project(tenant_id, project_id)
    return ProjectResponse.from_entity(project)


@router.get("", response_model=list[ProjectResponse])
def list_projects(tenant_id: str) -> list[ProjectResponse]:
    projects = project_service.list_projects(tenant_id)
    return [ProjectResponse.from_entity(p) for p in projects]


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, tenant_id: str) -> None:
    project_service.delete_project(tenant_id, project_id)
