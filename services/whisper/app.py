from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

app = FastAPI(title="SpeakNest Whisper STT", version="0.1.0")

_model: Any = None
_MODEL_NAME = "medium"


def load_model() -> Any:
    from faster_whisper import WhisperModel

    return WhisperModel(_MODEL_NAME, device="cpu", compute_type="int8")


@app.get("/health")
async def health():
    model_status = "not_loaded"
    if _model is not None:
        model_status = "loaded"
    return {"status": "ok", "model": _MODEL_NAME, "model_status": model_status}


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...), model: str | None = None, language: str | None = None):
    global _model

    if _model is None:
        _model = load_model()

    if not file.filename:
        return JSONResponse(status_code=400, content={"error": "No filename provided"})

    if model is None:
        model = _MODEL_NAME

    segments, info = _model.transcribe(file.filename, language=language, beam_size=5)
    transcript = "".join(segment.text for segment in segments)

    return {"text": transcript, "language_detected": info.language}


@app.get("/models")
async def get_models():
    return {"default_model": _MODEL_NAME}
