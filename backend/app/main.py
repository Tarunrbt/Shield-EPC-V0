from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.generate import router as generate_router
from app.api.incident_investigation import router as incident_investigation_router
from app.api.training_competency import router as training_competency_router
from app.api.health import router as health_router
from app.api.tenants import router as tenant_router
from app.api.projects import router as project_router
from core.exceptions import (
    ShieldEPCError,
    ValidationFailed,
    TenantNotFound,
    DocumentNotFound,
)

app = FastAPI(title="Shield EPC Backend", version="0.1.0")

# Phase 4 local-dev CORS: scoped to local origins only, not "*".
# "null" covers the Enterprise Console opened directly via file://.
# The 127.0.0.1/localhost entries cover a local static server (e.g.
# `python3 -m http.server 8080` in frontend/). Extend this list, do not
# widen to "*", when GitHub Pages / tunnel access is added in Phase 2 --
# that phase adds the specific public origin explicitly instead.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "null",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

# Phase 5B: map domain exceptions (core/exceptions.py) to HTTP responses.
# Endpoints (app/api/tenants.py, app/api/projects.py) deliberately do not
# catch these -- they propagate here so the mapping stays in one place.
_STATUS_BY_EXCEPTION = {
    ValidationFailed: 400,
    TenantNotFound: 404,
    DocumentNotFound: 404,
}


@app.exception_handler(ShieldEPCError)
def shield_epc_error_handler(request: Request, exc: ShieldEPCError) -> JSONResponse:
    status_code = 500
    for exc_type, code in _STATUS_BY_EXCEPTION.items():
        if isinstance(exc, exc_type):
            status_code = code
            break
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": str(exc.code), "message": exc.message}},
    )


app.include_router(health_router)
app.include_router(generate_router)
app.include_router(incident_investigation_router)
app.include_router(training_competency_router)
app.include_router(tenant_router)
app.include_router(project_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok"}
