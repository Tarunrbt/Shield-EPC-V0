from __future__ import annotations

from fastapi import FastAPI

from app.api.generate import router as generate_router
from app.api.health import router as health_router

app = FastAPI(title="Shield EPC Backend", version="0.1.0")

app.include_router(health_router)
app.include_router(generate_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok"}
