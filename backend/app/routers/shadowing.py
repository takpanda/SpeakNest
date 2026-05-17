"""Shadowing mode API endpoints.

GET /shadowing/sentences            – get practice sentences (category + level filter)
GET /shadowing/tts                  – get TTS audio for a target sentence
POST /shadowing/evaluate             – evaluate learner audio against target sentence
POST /shadowing/sessions             – persist a shadowing session result
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import get_tts_base_url
from app.pronunciation.eval import evaluate_pronunciation
from app.routers.chat_logic import ServiceUnavailableError
from app.db.repository import create_session, create_utterance, complete_session
from app.db.database import get_db
import httpx

router = APIRouter(prefix="/shadowing", tags=["shadowing"])

# ------
# Sentence master data
# ------

_SENTENCES_PATH = Path(__file__).parent.parent.parent.parent / "data" / "sentences.json"

_SENTENCES: list[dict] = []


def _load_sentences() -> list[dict]:
    global _SENTENCES
    if not _SENTENCES and _SENTENCES_PATH.exists():
        try:
            _SENTENCES = json.loads(_SENTENCES_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            _SENTENCES = []
    return _SENTENCES


# ------
# Request / response models
# ------


class EvaluateRequest(BaseModel):
    target_sentence: str = Field(..., description="目標文")
    transcript: str = Field(..., description="Whisper 書き起こし")
    sentence_mode: bool = Field(False)


class TtsRequest(BaseModel):
    text: str = Field(..., description="Synthesise this text")


class SentenceQuery(BaseModel):
    id: str
    category: str
    level: str
    text: str
    translation_ja: str


class SentencesResponse(BaseModel):
    sentences: list[SentenceQuery]


class EvaluateResponse(BaseModel):
    wer: float
    missing_words: list[str]
    extra_words: list[str]
    target_word_count: int
    transcript_word_count: int
    accuracy: float
    is_valid: bool


class SessionCreateRequest(BaseModel):
    session_id: str
    target_sentence: str
    transcript: str
    wer: float
    score: Optional[int] = None
    missing_words: list[str] = []
    extra_words: list[str] = []


class SessionCreateResponse(BaseModel):
    session_id: str
    saved: bool
    utterance_count: int


# ------
# Endpoints
# ------


@router.get(
    "/sentences",
    response_model=SentencesResponse,
    summary="Get practice sentences",
)
async def get_sentences(
    category: Optional[str] = Query(None, description="Category filter (daily, travel, business, tech)"),
    level: Optional[str] = Query(None, description="CEFR level filter (A1, A2, B1, B2)"),
):
    all_sentences = _load_sentences()
    filtered = all_sentences
    if category:
        filtered = [s for s in filtered if s.get("category") == category]
    if level:
        filtered = [s for s in filtered if s.get("level") == level]
    items = [
        SentenceQuery(
            id=s.get("id", ""),
            category=s.get("category", ""),
            level=s.get("level", ""),
            text=s.get("text", ""),
            translation_ja=s.get("translation_ja", ""),
        )
        for s in filtered
    ]
    return SentencesResponse(sentences=items)


@router.get(
    "/tts",
    summary="Get TTS audio for a target sentence",
)
async def get_ttsaudio(
    text: str = Query(..., description="Text to synthesise"),
):
    """Return TTS audio if Piper is available; otherwise a 503 with instructions."""
    tts_base = get_tts_base_url()
    if not tts_base:
        raise HTTPException(status_code=503, detail="TTS service is not configured. Set TTS_BASE_URL and start Piper.")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{tts_base.rstrip('/')}/synthesize", json={"text": text})
            if resp.status_code != 200:
                raise HTTPException(status_code=503, detail=f"TTS service error: {resp.status_code}")
            return resp.content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"TTS service unavailable: {e}")


@router.post(
    "/evaluate",
    response_model=EvaluateResponse,
    summary="Evaluate shadowing audio",
)
async def evaluate_shadowing(req: EvaluateRequest):
    result = evaluate_pronunciation(req.target_sentence, req.transcript, sentence_mode=req.sentence_mode)
    return EvaluateResponse(
        wer=result.wer,
        missing_words=result.missing_words,
        extra_words=result.extra_words,
        target_word_count=result.target_word_count,
        transcript_word_count=result.transcript_word_count,
        accuracy=result.accuracy,
        is_valid=result.is_valid,
    )


@router.post(
    "/sessions",
    response_model=SessionCreateResponse,
    summary="Persist a shadowing session result",
)
async def save_session(req: SessionCreateRequest):
    """Save a shadowing session and its utterance to DB."""
    # Check if session already exists
    from app.db.repository import get_session
    sess = get_session(req.session_id)
    if sess is None:
        sess = create_session(mode="shadowing", id=req.session_id)

    # Save utterance
    feedback = json.dumps({
        "wer": req.wer,
        "missing_words": req.missing_words,
        "extra_words": req.extra_words,
    })
    create_utterance(
        session_id=req.session_id,
        role="user",
        target_text=req.target_sentence,
        transcript=req.transcript,
        wer=req.wer,
        score=req.score,
        feedback_json=feedback,
        created_at=datetime.now(timezone.utc),
    )

    return SessionCreateResponse(session_id=req.session_id, saved=True, utterance_count=1)
