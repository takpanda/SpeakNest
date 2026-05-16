from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, UploadFile

from app.config import UPLOAD_DIR, settings
from app.routers.chat_logic import (
    ServiceUnavailableError,
    process_conversation,
)
from app.schemas import ChatRequest
from uuid import uuid4

router = APIRouter(prefix="/api", tags=["chat"])


@router.post(
    "/chat",
    response_model=None,
    summary="Process voice conversation",
    responses={
        200: {"description": "Conversation response with reply and feedback"},
        400: {"description": "Invalid input"},
        503: {"description": "STT or Ollama service unavailable"},
    },
)
async def chat(request: ChatRequest):
    """
    Process a voice conversation turn using JSON payload.
    """
    try:
        result = await process_conversation(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@router.post(
    "/conversation",
    response_model=None,
    summary="Process uploaded audio conversation",
    responses={
        200: {"description": "Conversation response with reply and feedback"},
        400: {"description": "Invalid input"},
        503: {"description": "STT or Ollama service unavailable"},
    },
)
async def conversation(
    audio: UploadFile,
    scene: str = Form(...),
    level: str = Form(...),
):
    """
    Receive audio, transcribe it, and process conversation.
    """
    allowed_types = settings.allowed_audio_mime_types.split(",")
    if audio.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {allowed_types}",
        )

    file_ext = audio.filename.split(".")[-1] if "." in audio.filename else "wav"
    filename = f"{uuid4().hex}.{file_ext}"
    filepath = UPLOAD_DIR / filename

    content = await audio.read()
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(content)

    request = ChatRequest(level=level, scenario=scene)

    try:
        result = await process_conversation(request, audio_path=str(filepath))
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
