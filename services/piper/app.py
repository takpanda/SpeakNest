"""Minimal Piper TTS HTTP wrapper.

Wraps the `piper` CLI binary (installed via piper-tts pip package) and exposes
a FastAPI endpoint POST /api/synthesize that forwards plain-text to the piper
bin and returns WAV audio bytes.
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

MODEL_PATH = "/models/en_US-ryan-high.onnx"

logger = logging.getLogger("piper")

app = FastAPI(title="Piper TTS")

_has_piper = bool(subprocess.run(["which", "piper"], capture_output=True).returncode == 0)


class _SynthReq(BaseModel):
    text: str


@app.on_event("startup")
async def _startup() -> None:
    if not _has_piper:
        logger.warning("piper binary not found on PATH – synthesize will return 503")
    model = Path(MODEL_PATH)
    meta = Path(MODEL_PATH + ".json")
    if not model.exists():
        raise RuntimeError(f"Piper model file missing: {model}")
    if not meta.exists():
        raise RuntimeError(f"Piper metadata file missing: {meta}")
    logger.info("Piper model loaded: %s", MODEL_PATH)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/synthesize")
async def synthesize(req: _SynthReq) -> bytes:
    if not _has_piper:
        raise HTTPException(status_code=503, detail="piper binary not available")
    if not req.text:
        raise HTTPException(status_code=400, detail="text is empty")

    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = Path(tmpdir) / "out.wav"
        proc = subprocess.run(
            ["piper", "--model", MODEL_PATH, "--output_file", str(wav_path)],
            input=req.text,
            capture_output=True,
            timeout=60,
        )
        if proc.returncode != 0:
            err = proc.stderr.decode(errors="replace")[:500]
            raise HTTPException(status_code=500, detail=err)
        return wav_path.read_bytes()
