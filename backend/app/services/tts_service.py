from __future__ import annotations

import httpx
from app.config import settings


class TtsError(Exception):
    pass


async def synthesize_text(text: str) -> bytes:
    """
    Synthesize text to speech via Piper TTS.

    Returns the WAV audio bytes on success.
    Raises TtsError if the Piper service is not responding.
    """
    base = settings.tts_base_url.rstrip("/")
    url = f"{base}/api/synthesize"

    headers = {"Content-Type": "text/plain"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, content=text, headers=headers)

    if resp.status_code != 200:
        detail = resp.text
        raise TtsError(f"TTS service returned {resp.status_code}: {detail}")

    return resp.content
