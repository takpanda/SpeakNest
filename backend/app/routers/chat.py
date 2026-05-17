from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, UploadFile
from uuid import uuid4

from app.config import UPLOAD_DIR, settings
from app.routers.chat_logic import (
    ServiceUnavailableError,
    process_conversation,
)
from app.schemas import ChatRequest, ConversationResponse

from app.db.repository import create_session, create_utterance, complete_session, list_utterances
from app.pronunciation.eval import evaluate_pronunciation
from app.services.weak_point_service import extract_weak_points
import json
from datetime import datetime, timezone

router = APIRouter(prefix="/api", tags=["chat"])


@router.post(
    "/chat",
    response_model=ConversationResponse,
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
    response_model=ConversationResponse,
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

    session_id = None
    try:
        # Process conversation (may raise)
        request = ChatRequest(scenario=scene, level=level)
        result = await process_conversation(request, audio_path=str(filepath))

        # Create session after success to avoid orphan sessions on failure
        db_session = create_session(mode="conversation", scenario=scene, level=level)
        session_id = db_session["id"]

        # Save user utterance
        create_utterance(
            session_id=session_id,
            role="user",
            transcript=result.transcript,
            created_at=datetime.now(timezone.utc),
        )

        # Save assistant utterance
        create_utterance(
            session_id=session_id,
            role="assistant",
            transcript=f"EN: {result.reply_en}\nJA: {result.reply_ja}",
            feedback_json=json.dumps({
                "feedback_ja": result.feedback_ja,
                "next_practice": result.next_practice,
            }),
            created_at=datetime.now(timezone.utc),
        )

        # Run WER evaluation and save as an utterance for scoring
        if result.transcript and result.next_practice:
            eval_result = evaluate_pronunciation(result.next_practice, result.transcript)
            create_utterance(
                session_id=session_id,
                role="system",
                target_text=result.next_practice,
                wer=eval_result.wer,
                score=int((1 - eval_result.wer) * 100) if eval_result.is_valid else None,
                created_at=datetime.now(timezone.utc),
            )

        # Extract weak points and mark session completed
        utter_list = list_utterances(session_id)
        extract_weak_points(utter_list, session_id)
        complete_session(session_id)

        return result
    except ValueError as e:
        # Clean up orphan session if it was created
        if session_id:
            complete_session(session_id)
        raise HTTPException(status_code=400, detail=str(e))
    except ServiceUnavailableError as e:
        if session_id:
            complete_session(session_id)
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        if session_id:
            complete_session(session_id)
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
    finally:
        filepath.unlink(missing_ok=True)
