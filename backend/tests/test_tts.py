from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.tts_service import TtsError


def _create_test_client():
    """Helper to create a fresh TestClient for each test."""
    return TestClient(app)


class TestTtsEndpoint:
    """Tests for POST /tts/synthesize."""

    def test_synthesize_returns_wav(self):
        """TTS returns audio/wav binary when Piper is available."""
        mock_wav = b"\x00fake_wav_data\x00"
        mock_async = AsyncMock(return_value=mock_wav)

        with patch("app.routers.tts.synthesize_text", mock_async):
            client = _create_test_client()
            res = client.post(
                "/tts/synthesize",
                json={"text": "Could you tell me how to get to the station?"},
            )
            assert res.status_code == 200
            assert "audio/wav" in res.headers["content-type"]
            assert res.content == mock_wav
            mock_async.assert_called_once_with("Could you tell me how to get to the station?")

    def test_synthesize_503_on_service_down(self):
        """TTS returns 503 when Piper service is down."""
        async def _raise(text):
            raise TtsError("TTS service unavailable")

        client = _create_test_client()
        with patch("app.routers.tts.synthesize_text", side_effect=_raise):
            res = client.post("/tts/synthesize", json={"text": "Hello"})
            assert res.status_code == 503
            assert "TTS service unavailable" in res.json()["detail"]

    def test_synthesize_rejects_empty_text(self):
        """Rejects empty text with 422."""
        client = _create_test_client()
        res = client.post("/tts/synthesize", json={"text": ""})
        assert res.status_code == 422
