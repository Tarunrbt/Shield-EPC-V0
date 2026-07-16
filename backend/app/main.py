from __future__ import annotations

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from app.api.generate import router as generate_router
from app.api.health import router as health_router

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
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(health_router)
app.include_router(generate_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok"}
