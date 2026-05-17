from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestSentencesEndpoint:
    """Tests for GET /shadowing/sentences."""

    def test_get_all_sentences(self, client):
        """All sentences when no filters applied."""
        res = client.get("/shadowing/sentences")
        assert res.status_code == 200
        data = res.json()
        assert "sentences" in data
        assert len(data["sentences"]) > 0

    def test_filter_by_category(self, client):
        """Filter to daily category only."""
        res = client.get("/shadowing/sentences?category=daily")
        assert res.status_code == 200
        sentences = res.json()["sentences"]
        for s in sentences:
            assert s["category"] == "daily"

    def test_filter_by_level(self, client):
        """Filter to A1 level only."""
        res = client.get("/shadowing/sentences?level=A1")
        assert res.status_code == 200
        sentences = res.json()["sentences"]
        for s in sentences:
            assert s["level"] == "A1"

    def test_filter_by_category_and_level(self, client):
        """Filter to travel category + B1 level."""
        res = client.get("/shadowing/sentences?category=travel&level=B1")
        assert res.status_code == 200
        sentences = res.json()["sentences"]
        for s in sentences:
            assert s["category"] == "travel"
            assert s["level"] == "B1"

    def test_sentence_fields(self, client):
        """Each sentence has required fields."""
        res = client.get("/shadowing/sentences")
        data = res.json()["sentences"][0]
        assert "id" in data
        assert "category" in data
        assert "level" in data
        assert "text" in data
        assert "translation_ja" in data

    def test_unknown_category_returns_empty(self, client):
        """Unknown category returns empty list."""
        res = client.get("/shadowing/sentences?category=unknown_xyz")
        assert res.status_code == 200
        sentences = res.json()["sentences"]
        assert len(sentences) == 0


class TestEvaluateEndpoint:
    """Tests for POST /shadowing/evaluate."""

    def test_evaluate_perfect_match(self, client):
        """Perfect match -> WER 0.0."""
        with patch("app.config.ollama_available", return_value=True):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(
                    return_value=httpx.Response(200, json={
                        "reply_en": "Great!",
                        "reply_ja": "素晴らしい！",
                        "feedback_ja": "完璧な発音です。",
                        "next_practice": "次の練習文に挑戦しましょう。",
                    })
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_cls.return_value = mock_client

                res = client.post(
                    "/shadowing/evaluate",
                    json={"target_sentence": "Hello world", "transcript": "Hello world"},
                )

        assert res.status_code == 200
        data = res.json()
        assert data["wer"] == 0.0
        assert data["accuracy"] == 1.0
        assert data["missing_words"] == []

    def test_evaluate_missing_words(self, client):
        """Part of text matched -> WER > 0."""
        with patch("app.config.ollama_available", return_value=True):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(
                    return_value=httpx.Response(200, json={
                        "reply_en": "Good try.",
                        "reply_ja": "頑張りました。",
                        "feedback_ja": "一部抜けがあります。",
                        "next_practice": "missing words を練習してください。",
                    })
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_cls.return_value = mock_client

                res = client.post(
                    "/shadowing/evaluate",
                    json={"target_sentence": "Hello world", "transcript": "Hello"},
                )

        assert res.status_code == 200
        data = res.json()
        assert data["wer"] > 0.0
        assert "world" in data["missing_words"]

    def test_evaluate_both_empty(self, client):
        """Both empty should return 400."""
        res = client.post(
            "/shadowing/evaluate",
            json={"target_sentence": "", "transcript": ""},
        )
        assert res.status_code == 400

    def test_evaluate_empty_transcript(self, client):
        """Empty transcript -> WER = 1.0."""
        with patch("app.config.ollama_available", return_value=True):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(
                    return_value=httpx.Response(200, json={
                        "reply_en": "",
                        "reply_ja": "",
                        "feedback_ja": "",
                        "next_practice": "",
                    })
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_cls.return_value = mock_client

                res = client.post(
                    "/shadowing/evaluate",
                    json={"target_sentence": "Hello world", "transcript": ""},
                )

        assert res.status_code == 200
        data = res.json()
        assert data["wer"] == 1.0

    def test_evaluate_response_fields(self, client):
        """Response has all required fields."""
        with patch("app.config.ollama_available", return_value=True):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(
                    return_value=httpx.Response(200, json={
                        "reply_en": "Great",
                        "reply_ja": "素晴らしい",
                        "feedback_ja": "良いです",
                        "next_practice": "続けましょう",
                    })
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_cls.return_value = mock_client

                res = client.post(
                    "/shadowing/evaluate",
                    json={"target_sentence": "Hello", "transcript": "Hello"},
                )

        assert res.status_code == 200
        data = res.json()
        assert "target_text" in data
        assert "transcript" in data
        assert "wer" in data
        assert "missing_words" in data
        assert "extra_words" in data
        assert "target_word_count" in data
        assert "transcript_word_count" in data
        assert "accuracy" in data
        assert "feedback_ja" in data
        assert "reply_en" in data
        assert "next_practice" in data


class TestSessionSaveEndpoint:
    """Tests for POST /shadowing/sessions."""

    def test_save_session(self, client):
        """Session saved successfully."""
        res = client.post(
            "/shadowing/sessions",
            json={
                "target_sentence": "Hello world",
                "transcript": "Hello world",
                "wer": 0.0,
                "feedback_ja": "完璧です。",
                "duration_seconds": 5.0,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["saved"] is True
        assert "session_id" in data

    def test_save_session_without_duration(self, client):
        """Session saved with optional duration=None."""
        res = client.post(
            "/shadowing/sessions",
            json={
                "target_sentence": "Hello world",
                "transcript": "Hello world",
                "wer": 0.5,
                "feedback_ja": "もう少しです。",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["saved"] is True


class TestTtsEndpoint:
    """Tests for GET /shadowing/tts."""

    def test_tts_unavailable(self, client):
        """TTS service down returns 503."""
        with patch("app.services.shadowing_service.fetch_tts_audio") as mock_fetch:
            mock_fetch.side_effect = Exception("TTS connection refused")
            res = client.get("/shadowing/tts?text=hello")
        assert res.status_code == 503
