import requests

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthCheckResponse(BaseModel):
    status: str
    ollama: str
    backend_port: int


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(backend_port: int = 8000):
    ollama_status = "unreachable"
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        if resp.status_code == 200:
            ollama_status = "connected"
    except Exception:
        ollama_status = "unreachable"

    return {
        "status": "healthy" if ollama_status == "connected" else "degraded",
        "ollama": ollama_status,
        "backend_port": backend_port,
    }
