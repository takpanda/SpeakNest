"""Pronunciation evaluation endpoint skeleton.

FastAPI router (placeholder) that exposes a simple ``POST /pronunciation``
endpoint.  The response mirrors the MVP acceptance criteria:
  - WER
  - missing_words
  - extra_words
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..pronunciation.eval import PronunciationResult, evaluate_pronunciation, build_llm_feedback_context_dict

router = APIRouter(prefix="/pronunciation", tags=["pronunciation"])


# ---------- request ----------

class PronunciationRequest(BaseModel):
    target_sentence: str = Field(..., min_length=0, description="目標文")
    transcript: str = Field(..., min_length=0, description="Whisper 書き起こし")
    sentence_mode: bool = Field(
        False, description="Target に文終わりがなければ評価を省略する"
    )


# ---------- response ----------

class PronunciationResponse(BaseModel):
    wer: float
    """WER [0.0, 1.0]"""
    missing_words: list[str]
    extra_words: list[str]
    target_word_count: int
    transcript_word_count: int
    accuracy: float
    is_valid: bool
    llm_context: dict = {}


# ---------- endpoint ----------

@router.post("/", response_model=PronunciationResponse)
async def evaluate(req: PronunciationRequest) -> PronunciationResponse:
    """Evaluate pronunciation given a target sentence and a transcript."""
    if not req.target_sentence and not req.transcript:
        raise HTTPException(
            status_code=400,
            detail="target_sentence と transcript の両方が空です",
        )

    target = req.target_sentence if req.target_sentence else ""
    transcript = req.transcript if req.transcript else ""

    result = evaluate_pronunciation(target, transcript, sentence_mode=req.sentence_mode)

    return PronunciationResponse(
        wer=result.wer,
        missing_words=result.missing_words,
        extra_words=result.extra_words,
        target_word_count=result.target_word_count,
        transcript_word_count=result.transcript_word_count,
        accuracy=result.accuracy,
        is_valid=result.is_valid,
        llm_context=build_llm_feedback_context_dict(target, result),
    )
