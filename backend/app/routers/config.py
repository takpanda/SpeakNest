import os
from pydantic import BaseModel

from fastapi import APIRouter

router = APIRouter()

EXPECTED_VARS = [
    "OLLAMA_BASE_URL",
    "WHISPER_BASE_URL",
    "TTS_BASE_URL",
    "DATA_DIR",
    "RECORDINGS_DIR",
    "DATABASE_URL",
    "CORS_ORIGINS",
]

DEFAULTS = {
    "ollama_base_url": "http://localhost:11434",
    "whisper_base_url": "http://localhost:8080",
    "tts_base_url": "http://localhost:5000",
    "data_dir": "./data",
    "recordings_dir": "./recordings",
    "database_url": "sqlite:///./data/speaknest.db",
    "cors_origins": ["http://localhost:3000"],
}
# env var -> settings attr mapping
ENV_TO_ATTR = {
    "OLLAMA_BASE_URL": "ollama_base_url",
    "WHISPER_BASE_URL": "whisper_base_url",
    "TTS_BASE_URL": "tts_base_url",
    "DATA_DIR": "data_dir",
    "RECORDINGS_DIR": "recordings_dir",
    "DATABASE_URL": "database_url",
    "CORS_ORIGINS": "cors_origins",
}


class ConfigResponse(BaseModel):
    configured: list[str]
    missing: list[str]


@router.get("/api/config", response_model=ConfigResponse)
async def get_config():
    configured = []
    missing = []
    for env_name in EXPECTED_VARS:
        attr = ENV_TO_ATTR[env_name]
        val = os.environ.get(env_name)
        if val:
            configured.append(env_name)
        else:
            missing.append(env_name)
    return {"configured": configured, "missing": missing}
