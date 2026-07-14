from fastapi import FastAPI

app = FastAPI(title="Shield EPC Backend", version="0.1.0")

@app.get("/")
def read_root():
    return {"status": "ok"}
from fastapi import FastAPI
from app.api.health import router as health_router

app = FastAPI(title="Shield EPC Backend", version="0.1.0")

app.include_router(health_router)

@app.get("/")
def read_root():
    return {"status": "ok"}
