import os
from pydantic import BaseModel

from fastapi import APIRouter

router = APIRouter()

EXPECTED_VARS = [
    "SPEAKNEST_OLLAMA_BASE_URL",
    "SPEAKNEST_STT_BASE_URL",
    "SPEAKNEST_UPLOAD_DIR",
    "SPEAKNEST_ALLOWED_AUDIO_MIME_TYPES",
    "SPEAKNEST_MAX_UPLOAD_SIZE_MB",
    "SPEAKNEST_DEFAULT_SCENARIO",
    "SPEAKNEST_CORS_ORIGINS",
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
    "SPEAKNEST_OLLAMA_BASE_URL": "ollama_base_url",
    "SPEAKNEST_STT_BASE_URL": "stt_base_url",
    "SPEAKNEST_UPLOAD_DIR": "upload_dir",
    "SPEAKNEST_ALLOWED_AUDIO_MIME_TYPES": "allowed_audio_mime_types",
    "SPEAKNEST_MAX_UPLOAD_SIZE_MB": "max_upload_size_mb",
    "SPEAKNEST_DEFAULT_SCENARIO": "default_scenario",
    "SPEAKNEST_CORS_ORIGINS": "cors_origins",
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
