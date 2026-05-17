from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {
        "env_prefix": "SPEAKNEST_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    # Application
    app_name: str = "SpeakNest"
    debug: bool = False

    # Ollama settings
    ollama_base_url: str = "http://192.168.1.103:11434"
    ollama_model: str = "gemma4:e4b"

    # STT settings (whisper.cpp)
    stt_base_url: str = "http://whisper:8000"
    stt_model: str = "medium"

    # TTS settings (piper)
    tts_base_url: str = "http://piper:5000"

    # Upload settings
    upload_dir: str = "data/recordings"
    allowed_audio_mime_types: str = "audio/webm,audio/wav,audio/mp4,audio/mpeg,audio/x-wav"
    max_upload_size_mb: int = 30

    # Conversation
    default_scenario: str = "カフェで注文する"
    default_level: str = "A2"

    # CORS
    cors_origins: str = "*"


settings = Settings()
UPLOAD_DIR = Path(settings.upload_dir)


def ensure_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def ollama_available() -> bool:
    """Check if Ollama is reachable."""
    import httpx

    base = settings.ollama_base_url.rstrip("/")
    try:
        resp = httpx.get(f"{base}/api/tags", timeout=3.0)
        return resp.status_code == 200
    except httpx.RequestError:
        return False


def stt_available() -> bool:
    """Check if STT service is reachable."""
    import httpx

    base = settings.stt_base_url.rstrip("/")
    try:
        resp = httpx.get(f"{base}/health", timeout=3.0)
        return resp.status_code == 200
    except httpx.RequestError:
        return False


def tts_available() -> bool:
    """Check if TTS (Piper) service is reachable."""
    import httpx

    base = settings.tts_base_url.rstrip("/")
    try:
        resp = httpx.get(f"{base}/api/health", timeout=3.0)
        return resp.status_code == 200
    except httpx.RequestError:
        return False
