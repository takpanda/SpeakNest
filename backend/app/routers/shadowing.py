"""Shadowing mode API router.

Endpoints:
  GET /shadowing/sentences     - List practice sentences (filterable by category/level)
  GET /shadowing/tts            - Generate reference audio via Piper TTS
  POST /shadowing/evaluate      - Evaluate user recording (STT + WER + LLM feedback)
  POST /shadowing/sessions      - Save session result (stub for future DB persistence)
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.config import settings
from app.services.shadowing_service import (
    shadowing_prompt_template,
    ShadowingResult,
    ShadowingSentence,
    evaluate_shadowing,
    fetch_tts_audio,
    load_sentences,
)

router = APIRouter(prefix="/shadowing", tags=["shadowing"])


# ---- Request/Response models ----

class SentenceResponse(BaseModel):
    id: str
    category: str
    level: str
    text: str
    translation_ja: str


class SentencesResponse(BaseModel):
    sentences: list[SentenceResponse]


class TtsResponse(BaseModel):
    """TTS endpoint returns raw audio (application/octet-stream or audio/wav)."""
    duration: float = -1
    mime_type: str = "audio/wav"


class EvaluateRequest(BaseModel):
    target_sentence: str = Field(..., description="目標文")
    transcript: str = Field(..., description="STTによるユーザーの発話書き起こし")


class EvaluateResponse(BaseModel):
    target_text: str
    transcript: str
    wer: float
    missing_words: list[str]
    extra_words: list[str]
    target_word_count: int
    transcript_word_count: int
    accuracy: float
    feedback_ja: str
    reply_en: str
    next_practice: str


class SessionSaveRequest(BaseModel):
    target_sentence: str = Field(..., description="目標文")
    transcript: str = Field(..., description="STTによるユーザーの発話書き起こし")
    wer: float = Field(..., description="WERスコア")
    feedback_ja: str = Field(..., description="LLMフィードバック")
    duration_seconds: Optional[float] = Field(None, description="録音の長さ")


class SessionSaveResponse(BaseModel):
    session_id: str
    saved: bool


# ---- GET /shadowing/sentences ----

@router.get("/sentences", response_model=SentencesResponse)
async def get_sentences(
    category: Optional[str] = Query(None, description="カテゴリで絞り込み (daily, travel, business, tech)"),
    level: Optional[str] = Query(None, description="CEFRレベルで絞り込み (A1, A2, B1, B2)"),
):
    """練習文リストを取得。category / level で絞り込み可能。"""
    sentences = load_sentences(category=category, level=level)
    return SentencesResponse(
        sentences=[
            SentenceResponse(
                id=s.id,
                category=s.category,
                level=s.level,
                text=s.text,
                translation_ja=s.translation_ja,
            )
            for s in sentences
        ]
    )


# ---- GET /shadowing/tts ----

@router.get(
    "/tts",
    response_class=Response,
    summary="お手本音声の生成",
    responses={
        200: {"content": {"audio/wav": {}}, "description": "Generated audio file"},
        400: {"description": "Text is empty"},
        503: {"description": "TTS service unavailable"},
    },
)
async def get_tts(text: str = Query(..., min_length=1, description="音声化するテキスト")):
    try:
        audio_data = await fetch_tts_audio(text)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"TTS service unavailable: {e}")

    return Response(content=audio_data, media_type="audio/wav")


# ---- POST /shadowing/evaluate ----

@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(req: EvaluateRequest):
    """ユーザーの発話を評価: WER + LLMフィードバック."""
    if not req.target_sentence and not req.transcript:
        raise HTTPException(status_code=400, detail="target_sentence と transcript の両方が空です")

    target = req.target_sentence if req.target_sentence else ""
    transcript = req.transcript if req.transcript else ""
    target_words = len(target.split()) if target else 0
    transcript_words = len(transcript.split()) if transcript else 0

    feedback_prompt = shadowing_prompt_template.format(
        target_text=target,
        user_utterance=transcript,
        wer=0.0,
        accuracy=1.0,
    )

    result: ShadowingResult = await evaluate_shadowing(target, transcript, feedback_prompt)

    return EvaluateResponse(
        target_text=result.target_text,
        transcript=result.transcript,
        wer=result.wer,
        missing_words=result.missing_words,
        extra_words=result.extra_words,
        target_word_count=result.target_word_count,
        transcript_word_count=result.transcript_word_count,
        accuracy=result.accuracy,
        feedback_ja=result.feedback_ja,
        reply_en=result.reply_en,
        next_practice=result.next_practice,
    )


# ---- POST /shadowing/sessions ----

@router.post("/sessions", response_model=SessionSaveResponse)
async def save_session(req: SessionSaveRequest):
    """セッション結果を保存。Phase 3でDB接続時に実装。Phase 2ではファイルに保存."""
    sessions_dir = Path("./data/shadowing_sessions")
    sessions_dir.mkdir(parents=True, exist_ok=True)

    session_id = str(uuid.uuid4())
    session_data = req.model_dump()
    session_data["session_id"] = session_id
    session_path = sessions_dir / f"{session_id}.json"

    with open(session_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

    return SessionSaveResponse(session_id=session_id, saved=True)
