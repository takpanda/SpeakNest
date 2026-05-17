from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.tts_service import TtsError, synthesize_text

router = APIRouter(prefix="/tts", tags=["tts"])


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize to speech")


@router.post("/synthesize", response_class=Response)
async def synthesize(request: SynthesizeRequest):
    """Synthesize text to speech (returns WAV audio)."""
    try:
        audio_bytes = await synthesize_text(request.text)
        return Response(content=audio_bytes, media_type="audio/wav")
    except TtsError as e:
        raise HTTPException(status_code=503, detail=str(e))
