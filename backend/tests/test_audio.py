from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestAudioUpload:
    """Tests for POST /api/audio/upload."""

    def test_upload_wav(self, client):
        """Happy path: upload a WAV file."""
        res = client.post(
            "/api/audio/upload",
            files={"file": ("test.wav", b"fake_wav_data", "audio/wav")},
        )
        assert res.status_code == 200
        data = res.json()
        assert "file_id" in data
        assert "file_path" in data
        assert "size" in data
        assert data["mime_type"] == "audio/wav"

    def test_upload_webm(self, client):
        """Happy path: upload a WEBM file."""
        res = client.post(
            "/api/audio/upload",
            files={"file": ("test.webm", b"fake_webm_data", "audio/webm")},
        )
        assert res.status_code == 200
        assert res.json()["mime_type"] == "audio/webm"

    def test_upload_unsupported_mime(self, client):
        """400 for unsupported file type."""
        res = client.post(
            "/api/audio/upload",
            files={"file": ("test.pdf", b"fake_pdf", "application/pdf")},
        )
        assert res.status_code == 400

    def test_upload_empty_file(self, client):
        """400 for empty file."""
        res = client.post(
            "/api/audio/upload",
            files={"file": ("test.wav", b"", "audio/wav")},
        )
        assert res.status_code == 400

    def test_get_file_not_found(self, client):
        """404 for non-existent file."""
        res = client.get("/api/audio/uploads/nonexistent.wav")
        assert res.status_code == 404
