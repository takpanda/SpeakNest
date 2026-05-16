from __future__ import annotations

from unittest.mock import AsyncMock, patch
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import UPLOAD_DIR, ollama_available


class TestChatEndpoint:
    """Tests for POST /api/chat."""

    def test_chat_with_transcript(self, client):
        """Happy path: transcript provided, Ollama replies."""
        mock_response = {
            "reply_en": "Sure! What would you like?",
            "reply_ja": "はい、何にしますか？",
            "feedback_ja": "完璧です。",
            "next_practice": "I'd like a cappuccino.",
        }

        def _mock_post(url, json=None, **kw):
            return httpx.Response(200, json=mock_response)

        with patch("app.config.ollama_available", return_value=True):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(side_effect=lambda *a, **k: _mock_post(None))
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_cls.return_value = mock_client

                res = client.post(
                    "/api/chat/",
                    json={"level": "A2", "scenario": "カフェで注文する", "transcript": "I would like a coffee"},
                )

        assert res.status_code == 200
        data = res.json()
        assert data["transcript"] == "I would like a coffee"
        assert data["reply_en"] == "Sure! What would you like?"
        assert data["reply_ja"] == "はい、何にしますか？"
        assert "feedback_ja" in data
        assert "next_practice" in data

    def test_chat_missing_transcript_no_audio(self, client):
        """400 when transcript is None and no audio given."""
        res = client.post(
            "/api/chat/",
            json={"level": "A2", "scenario": "カフェで注文する"},
        )
        assert res.status_code == 400

    def test_chat_empty_transcript(self, client):
        """400 when transcript is empty string."""
        res = client.post(
            "/api/chat/",
            json={"level": "A2", "scenario": "カフェで注文する", "transcript": ""},
        )
        assert res.status_code == 400

    def test_chat_ollama_unavailable(self, client):
        """503 when Ollama is not reachable."""
        with patch("app.config.ollama_available", return_value=False):
            res = client.post(
                "/api/chat/",
                json={"level": "A2", "scenario": "カフェで注文する", "transcript": "hello"},
            )
        assert res.status_code == 503
