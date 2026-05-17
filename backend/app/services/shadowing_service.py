from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings as app_settings
from app.pronunciation.eval import evaluate_pronunciation, PronunciationResult
from app.services.ollama_service import generate_conversation, _OllamaError

SENTENCES_PATH = Path(__file__).parent.parent / "data" / "sentences.json"
SHADOWING_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "shadowing.md"


class _TtsError(Exception):
    pass


class _ShadowingError(Exception):
    pass


@dataclass
class ShadowingSentence:
    id: str
    category: str
    level: str
    text: str
    translation_ja: str


@dataclass
class ShadowingResult:
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


def _load_prompt(path: Path) -> str:
    """Load prompt text from file, return empty string if missing."""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


shadowing_prompt_template = _load_prompt(SHADOWING_PROMPT_PATH)


def load_sentences(category: Optional[str] = None, level: Optional[str] = None) -> list[ShadowingSentence]:
    """Load sentences from the JSON master file, optionally filtered by category and level."""
    if not SENTENCES_PATH.exists():
        return []

    with open(SENTENCES_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    sentences = [
        ShadowingSentence(
            id=s["id"],
            category=s["category"],
            level=s["level"],
            text=s["text"],
            translation_ja=s["translation_ja"],
        )
        for s in raw
    ]

    if category:
        sentences = [s for s in sentences if s.category == category]
    if level:
        sentences = [s for s in sentences if s.level == level]

    return sentences


def _normalise(text: str) -> str:
    """Normalise text for TTS request (strip extra whitespace)."""
    return " ".join(text.split())


async def fetch_tts_audio(text: str) -> bytes:
    """Call Piper TTS API to generate reference audio for the given text.

    Returns raw audio bytes (WAV format).
    Raises _TtsError if the TTS service is unavailable.
    """
    base = app_settings.tts_base_url.rstrip("/")
    url = f"{base}/tts"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json={"text": _normalise(text)})

    if resp.status_code != 200:
        detail = resp.text
        raise _TtsError(f"TTS service returned {resp.status_code}: {detail}")

    content_type = resp.headers.get("content-type", "")
    if "audio" not in content_type:
        raise _TtsError(f"Unexpected TTS response content-type: {content_type}")

    return resp.content


async def evaluate_shadowing(
    target_sentence: str,
    transcript: str,
    feedback_prompt: str,
) -> ShadowingResult:
    """Evaluate a shadowing attempt: WER calculation + LLM feedback.

    Parameters
    ----------
    target_sentence : str
        The reference sentence (target text).
    transcript : str
        The STT transcription of the learner's utterance.
    feedback_prompt : str
        The prompt to send to Ollama for feedback generation.

    Returns
    -------
    ShadowingResult
    """
    # 1. WER calculation
    result: PronunciationResult = evaluate_pronunciation(target_sentence, transcript)

    # 2. LLM feedback
    feedback_ja = ""
    reply_en = ""
    next_practice = ""

    try:
        resp = await generate_conversation(feedback_prompt)
        feedback_ja = resp.get("feedback_ja", "")
        reply_en = resp.get("reply_en", "")
        next_practice = resp.get("next_practice", "")
    except _OllamaError:
        pass

    extra = result.extra_words if result.extra_words else []
    missing = result.missing_words if result.missing_words else []

    return ShadowingResult(
        target_text=target_sentence,
        transcript=transcript,
        wer=result.wer,
        missing_words=missing,
        extra_words=extra,
        target_word_count=result.target_word_count,
        transcript_word_count=result.transcript_word_count,
        accuracy=result.accuracy,
        feedback_ja=feedback_ja,
        reply_en=reply_en,
        next_practice=next_practice,
    )
