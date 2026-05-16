from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.routers import (
    ServiceUnavailableError,
    process_conversation,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post(
    "/",
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
    Process a voice conversation turn.

    Accepts transcript (pre-transcribed) or expect an audio file upload
    (handled via multipart form data). This endpoint handles only the
    JSON body. For audio upload, use the upload endpoint separately.
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
