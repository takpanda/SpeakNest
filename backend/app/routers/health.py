from __future__ import annotations

from app.config import settings
from app.schemas import HealthResponse
from app.config import ollama_available, stt_available

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint returning STT and Ollama status."""
    o_ready = "ok" if ollama_available() else "not_available"
    s_ready = "ok" if stt_available() else "not_available"

    return HealthResponse(
        status="ok",
        ollama=o_ready,
        stt=s_ready,
        upload_dir=str(settings.upload_dir),
    )
