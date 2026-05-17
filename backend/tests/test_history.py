"""Tests for history and review API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from uuid import uuid4 as _uuid

import pytest
from fastapi.testclient import TestClient

from app.db.repository import create_session, create_utterance, upsert_weak_point
from app.main import app


@pytest.fixture
def sample_session():
    """Create a sample session + utterances for testing."""
    sess = create_session(mode="conversation", scenario="テスト", level="A2")
    session_id = sess["id"]
    ts = datetime.now(timezone.utc)
    create_utterance(
        session_id=session_id,
        role="user",
        transcript="Hello world",
        target_text="Hello world",
        wer=0.0,
        score=100,
        created_at=ts,
    )
    create_utterance(
        session_id=session_id,
        role="assistant",
        transcript="Hi there!",
        feedback_json='{"feedback_ja": "good"}',
        created_at=ts,
    )
    return session_id


class TestSessionsEndpoint:
    """Tests for GET /history/sessions."""

    def test_list_returns_sessions_with_data(self, sample_session):
        """Returns sessions when data exists."""
        client = TestClient(app)
        res = client.get("/history/sessions")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        assert len(data["sessions"]) >= 1
        assert data["sessions"][0]["mode"] == "conversation"

    def test_list_with_pagination(self, sample_session):
        """Respects page and page_size parameters."""
        client = TestClient(app)
        res = client.get("/history/sessions", params={"page": 1, "page_size": 1})
        assert res.status_code == 200
        assert len(res.json()["sessions"]) <= 1

    def test_list_with_mode_filter(self, sample_session):
        """Filters by mode correctly."""
        client = TestClient(app)
        res = client.get("/history/sessions", params={"mode": "conversation"})
        assert res.status_code == 200
        sessions = res.json()["sessions"] or []
        assert len(sessions) >= 1


class TestSessionDetailEndpoint:
    """Tests for GET /history/sessions/{id}."""

    def test_list_returns_structure(self):
        """Returns valid structure with data."""
        client = TestClient(app)
        res = client.get("/history/sessions")
        assert res.status_code == 200
        data = res.json()
        assert "sessions" in data
        assert "total" in data
        assert isinstance(data["sessions"], list)
        assert isinstance(data["total"], int)

    def test_detail_not_found(self):
        """404 for non-existent session."""
        client = TestClient(app)
        res = client.get(f"/history/sessions/{_uuid()}")
        assert res.status_code == 404

    def test_detail_returns_utterances(self, sample_session):
        """Returns session detail with utterances."""
        client = TestClient(app)
        res = client.get(f"/history/sessions/{sample_session}")
        assert res.status_code == 200
        data = res.json()
        assert "session" in data
        assert "utterances" in data
        assert len(data["utterances"]) >= 1


class TestWeakPointsEndpoint:
    """Tests for GET /history/weak-points."""

    def test_returns_weak_points_with_data(self):
        """Returns weak points when data exists."""
        client = TestClient(app)
        unique_phrase = f"test-wp-{_uuid().hex[:8]}"
        upsert_weak_point(phrase=unique_phrase, issue_type="missing")
        res = client.get("/history/weak-points")
        assert res.status_code == 200
        phrases = [wp["phrase"] for wp in res.json()]
        assert unique_phrase in phrases


class TestReviewEndpoint:
    """Tests for GET /history/review/next."""

    def test_returns_a_review_problem(self):
        """Returns a review problem when weak points exist."""
        client = TestClient(app)
        unique_phrase = f"test-review-{_uuid().hex[:8]}"
        upsert_weak_point(phrase=unique_phrase, issue_type="missing")
        res = client.get("/history/review/next")
        assert res.status_code == 200
        data = res.json()
        assert "weak_point" in data
        assert data["weak_point"]["phrase"] == unique_phrase


class TestSessionNoSideEffect:
    """Verify GET /history/sessions/{id} does NOT have side effects."""

    def test_get_does_not_set_ended_at(self):
        """GET should NOT alter ended_at."""
        from app.db.repository import get_session
        client = TestClient(app)
        ts = datetime.now(timezone.utc) - timedelta(hours=1)
        sess = create_session(mode="conversation", scenario="テスト", level="A1", started_at=ts)
        sid = sess["id"]
        initial_ended = sess["ended_at"]

        res = client.get(f"/history/sessions/{sid}")
        assert res.status_code == 200

        updated = get_session(sid)
        assert initial_ended == updated["ended_at"]
