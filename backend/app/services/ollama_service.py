from __future__ import annotations

import httpx
from app.config import settings as app_settings


async def generate_conversation(prompt_text: str) -> dict:
    """
    Call Ollama API to generate conversation reply + feedback.

    Returns dict with keys:
      - reply_en
      - reply_ja
      - feedback_ja
      - next_practice
    """
    base = app_settings.ollama_base_url.rstrip("/")
    url = f"{base}/api/generate"

    payload = {
        "model": app_settings.ollama_model,
        "prompt": prompt_text,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=payload)

    if resp.status_code != 200:
        detail = resp.text
        raise _OllamaError(f"Ollama API returned {resp.status_code}: {detail}")

    body = resp.json()
    generated_text = body.get("response", "")

    # Parse JSON from Ollama response
    reply = _parse_ollama_output(generated_text)

    # Fallback: empty strings if parsing fails
    return {
        "reply_en": reply.get("reply_en", ""),
        "reply_ja": reply.get("reply_ja", ""),
        "feedback_ja": reply.get("feedback_ja", ""),
        "next_practice": reply.get("next_practice", ""),
    }


def _parse_ollama_output(text: str) -> dict:
    """
    Parse Ollama's text output into JSON with expected fields.
    """
    import json

    text = text.strip()

    # Try as-is first
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # Look for ```json ... ``` block
    if "```json" in text:
        parts = text.split("```json")
        if len(parts) >= 2:
            snippet = parts[1].split("```")[0].strip()
            try:
                return json.loads(snippet)
            except (json.JSONDecodeError, TypeError):
                pass

    return {}


class _OllamaError(Exception):
    pass
