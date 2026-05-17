from __future__ import annotations

import sys
import uuid as uuid_module
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session as SASession

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.models import Base, Session as SessionModel, Utterance, WeakPoint
from app.db.repository import (
    create_session,
    end_session,
    get_session,
    list_sessions,
    create_utterance,
    get_utterance,
    list_utterances,
    delete_utterance,
    upsert_weak_point,
    get_weak_points,
    get_weak_point,
)


@pytest.fixture()
def db_engine():
    """Create an in-memory SQLite engine for testing."""
    return create_engine("sqlite:///:memory:")


@pytest.fixture()
def db_session(db_engine):
    """Create a database session for each test."""
    Base.metadata.create_all(bind=db_engine)
    session = SASession(bind=db_engine)
    yield session
    session.close()
    Base.metadata.drop_all(bind=db_engine)


class TestSessionCRUD:
    def test_create_session(self, db_session):
        session = create_session(db_session, mode="conversation")
        uuid_module.UUID(session.id)
        assert session.mode == "conversation"
        assert session.scenario is None
        assert session.ended_at is None

    def test_create_session_with_scenario(self, db_session):
        session = create_session(db_session, mode="shadowing", scenario="空港で", level="B1")
        assert session.mode == "shadowing"
        assert session.scenario == "空港で"
        assert session.level == "B1"

    def test_get_session(self, db_session):
        session = create_session(db_session, mode="conversation")
        found = get_session(db_session, session.id)
        assert found is not None
        assert found.id == session.id

    def test_get_session_not_found(self, db_session):
        assert get_session(db_session, "nonexistent") is None

    def test_list_sessions(self, db_session):
        for i in range(5):
            create_session(db_session, mode="conversation")
        assert len(list_sessions(db_session)) == 5

    def test_list_sessions_with_mode_filter(self, db_session):
        create_session(db_session, mode="conversation")
        create_session(db_session, mode="shadowing")
        create_session(db_session, mode="shadowing")
        assert len(list_sessions(db_session, mode="conversation")) == 1
        assert len(list_sessions(db_session, mode="shadowing")) == 2

    def test_list_sessions_pagination(self, db_session):
        for i in range(5):
            create_session(db_session, mode="conversation")
        first_page = list_sessions(db_session, limit=2, offset=0)
        second_page = list_sessions(db_session, limit=2, offset=2)
        assert len(first_page) == 2
        assert len(second_page) == 2

    def test_end_session(self, db_session):
        session = create_session(db_session, mode="conversation")
        ended = end_session(db_session, session.id)
        assert ended is not None
        assert ended.ended_at is not None

    def test_end_session_not_found(self, db_session):
        assert end_session(db_session, "nonexistent") is None


class TestUtteranceCRUD:
    def test_create_utterance(self, db_session):
        session = create_session(db_session, mode="conversation")
        utt = create_utterance(db_session, session_id=session.id, role="user", transcript="Hello")
        uuid_module.UUID(utt.id)
        assert utt.session_id == session.id
        assert utt.role == "user"
        assert utt.transcript == "Hello"

    def test_get_utterance(self, db_session):
        session = create_session(db_session, mode="conversation")
        utt = create_utterance(db_session, session_id=session.id, role="user", transcript="Hello")
        found = get_utterance(db_session, utt.id)
        assert found is not None
        assert found.id == utt.id

    def test_get_utterance_not_found(self, db_session):
        assert get_utterance(db_session, "nonexistent") is None

    def test_list_utterances(self, db_session):
        session = create_session(db_session, mode="conversation")
        for i in range(3):
            create_utterance(db_session, session_id=session.id, role="user", transcript=f"Message {i}")
        assert len(list_utterances(db_session, session.id)) == 3

    def test_list_utterances_pagination(self, db_session):
        session = create_session(db_session, mode="conversation")
        for i in range(5):
            create_utterance(db_session, session_id=session.id, role="user", transcript=f"M{i}")
        page = list_utterances(db_session, session.id, limit=3, offset=2)
        assert len(page) == 3

    def test_delete_utterance(self, db_session):
        session = create_session(db_session, mode="conversation")
        utt = create_utterance(db_session, session_id=session.id, role="user", transcript="Delete me")
        assert delete_utterance(db_session, utt.id) is True
        assert get_utterance(db_session, utt.id) is None

    def test_delete_utterance_not_found(self, db_session):
        assert delete_utterance(db_session, "nonexistent") is False


class TestWeakPointCRUD:
    def test_create_weak_point(self, db_session):
        wp = upsert_weak_point(db_session, phrase="Could I have", issue_type="missing")
        uuid_module.UUID(wp.id)
        assert wp.phrase == "Could I have"
        assert wp.issue_type == "missing"
        assert wp.count == 1

    def test_upsert_increments_count(self, db_session):
        wp = upsert_weak_point(db_session, phrase="Could I have", issue_type="missing")
        assert wp.count == 1
        wp2 = upsert_weak_point(db_session, phrase="Could I have", issue_type="missing")
        assert wp2.count == 2

    def test_upsert_ignores_issue_type_update(self, db_session):
        """Existing record's issue_type is not changed by upsert."""
        wp = upsert_weak_point(db_session, phrase="test phrase", issue_type="missing")
        wp2 = upsert_weak_point(db_session, phrase="test phrase", issue_type="slow")
        assert wp2.issue_type == "missing"
        assert wp2.count == 2

    def test_get_weak_points(self, db_session):
        upsert_weak_point(db_session, phrase="A", issue_type="missing")
        upsert_weak_point(db_session, phrase="B", issue_type="slow")
        assert len(get_weak_points(db_session)) == 2

    def test_get_weak_points_filtered_by_type(self, db_session):
        upsert_weak_point(db_session, phrase="A", issue_type="missing")
        upsert_weak_point(db_session, phrase="B", issue_type="missing")
        upsert_weak_point(db_session, phrase="C", issue_type="slow")
        assert len(get_weak_points(db_session, issue_type="missing")) == 2
        assert len(get_weak_points(db_session, issue_type="slow")) == 1

    def test_get_weak_point(self, db_session):
        wp = upsert_weak_point(db_session, phrase="test", issue_type="missing")
        found = get_weak_point(db_session, wp.id)
        assert found is not None
        assert found.id == wp.id

    def test_get_weak_point_not_found(self, db_session):
        assert get_weak_point(db_session, "nonexistent") is None
