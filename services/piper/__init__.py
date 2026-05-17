from __future__ import annotations

import subprocess
import typing as t

if t.TYPE_CHECKING:
    from fastapi import FastAPI

MODEL_PATH = "/models/en_US-ryan-high.onnx"

app: t.Union[t.Any, None] = None


def _get_app() -> "FastAPI":
    if app is None:
        raise RuntimeError("Piper service is not initialized")
    return app


async def startup() -> None:
    import json
    from pathlib import Path

    # Verify model files exist
    model = Path(MODEL_PATH)
    meta = Path(MODEL_PATH + ".json")
    if not model.exists():
        raise RuntimeError(f"Piper model not found: {model}")
    if not meta.exists():
        raise RuntimeError(f"Piper metadata not found: {meta}")


async def shutdown() -> None:
    global app
    app = None
