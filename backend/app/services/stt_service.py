from __future__ import annotations

import httpx
from app.config import settings as app_settings


async def transcribe_audio(file_path: str) -> str:
    """
    Transcribe audio file via local STT service (whisper.cpp).

    Returns transcript text.
    Raises _SttError if STT service is not responding.
    """
    base = app_settings.stt_base_url.rstrip("/")
    url = f"{base}/api/transcribe"

    with open(file_path, "rb") as f:
        files = {"file": (file_path.split("/")[-1], f, "audio/wav")}
        data = {"model": app_settings.stt_model, "language": "en"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, files=files, data=data)

    if resp.status_code != 200:
        detail = resp.text
        raise _SttError(f"STT service returned {resp.status_code}: {detail}")

    body = resp.json()
    # Whisper API compatible format: {"text": "..."}
    return body.get("text", "")


class _SttError(Exception):
    pass
