from __future__ import annotations

import os
import uuid
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse as _FileResponse

from app.config import settings, UPLOAD_DIR

router = APIRouter(prefix="/api/audio", tags=["audio"])


# MIME types that are allowed for upload
ALLOWED_MIME_TYPES: List[str] = settings.allowed_audio_mime_types.split(",")


@router.post(
    "/upload",
    summary="Upload audio file for transcription",
    responses={
        200: {"description": "Audio file saved successfully"},
        400: {"description": "Invalid file type or upload error"},
        500: {"description": "Storage error"},
    },
)
async def upload_audio(file: UploadFile):
    """
    Receive an audio file and save it locally.

    Returns the file path and a transcript preview (empty until STT processes it).
    STT processing is done by a separate /api/chat endpoint.
    """
    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {ALLOWED_MIME_TYPES}",
        )

    # Validate file size (max 30 MB)
    file_bytes = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB",
        )

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Save file
    filename = f"{uuid.uuid4().hex}.wav"
    filepath = UPLOAD_DIR / filename

    with open(filepath, "wb") as f:
        f.write(file_bytes)

    return {
        "file_id": filename,
        "file_path": str(filepath),
        "size": len(file_bytes),
        "mime_type": file.content_type,
    }


@router.get("/uploads/{file_id}")
async def get_uploaded_file(file_id: str) -> _FileResponse:
    """Retrieve a previously uploaded audio file."""
    filepath = UPLOAD_DIR / file_id
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return _FileResponse(filepath)
