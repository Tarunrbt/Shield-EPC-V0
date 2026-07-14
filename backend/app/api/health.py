"""
Health check endpoint.

Used for liveness/readiness probes (load balancers, container
orchestration, uptime monitoring). Deliberately has no dependencies
on AuditLog, Orchestrator, or any agent -- it must respond even if
those subsystems are degraded, so it can't share their failure modes.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
