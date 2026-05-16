from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

# Ensure tests import the local backend package first.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app
from app.config import UPLOAD_DIR


@pytest.fixture(autouse=True)
def _ensure_upload_dir():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def _mock_ollama(client):
    """Mock Ollama responses for all tests."""
    mock_response = {
        "reply_en": "Sure! What would you like to order?",
        "reply_ja": "はい！何を注文しますか？",
        "feedback_ja": "自然な表現です。",
        "next_practice": "Could I have a latte?",
    }

    def _side_effect(url, **kwargs):
        mock_resp = httpx.Response(200, json=mock_response)
        return mock_resp

    with patch("httpx.AsyncClient", autospec=True) as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=lambda *args, **kw: _side_effect(None))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        with patch("app.config.ollama_available", return_value=True):
            with patch("app.config.stt_available", return_value=True):
                yield mock_client


@pytest.fixture()
def mock_audio_file():
    """Return bytes of a minimal WAV-like file (not real WAV, just for upload testing)."""
    return b"fake_audio_data"
