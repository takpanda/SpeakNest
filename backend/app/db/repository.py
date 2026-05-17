"""CRUD repository layer for SpeakNest.

All public methods accept and return plain dicts (no SQLAlchemy model instances
are exposed outside this module).  The repository uses the global ``SessionLocal``
from ``app.db.database`` directly so callers do not need a DB dependency.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func

from app.db.database import SessionLocal
from app.db.models import Session as SessionModel
from app.db.models import Utterance as UtteranceModel
from app.db.models import WeakPoint as WeakPointModel


def _to_session(row: SessionModel) -> Dict:
    return row.as_dict()


def _to_utterance(row: UtteranceModel) -> Dict:
    return row.as_dict()


def _to_weak_point(row: WeakPointModel) -> Dict:
    return row.as_dict()


# --- Sessions ---


def create_session(mode: str = "conversation", **kwargs) -> Dict:
    db = SessionLocal()
    try:
        session = SessionModel(mode=mode, **kwargs)
        db.add(session)
        db.commit()
        db.refresh(session)
        return _to_session(session)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_session(session_id: str) -> Optional[Dict]:
    db = SessionLocal()
    try:
        row = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        return _to_session(row) if row else None
    finally:
        db.close()


def list_sessions(
    mode: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict:
    """Return (items, total_count) ordered by started_at DESC."""
    db = SessionLocal()
    try:
        q = db.query(SessionModel)
        if mode:
            q = q.filter(SessionModel.mode == mode)
        total = q.count()
        items = (
            q.order_by(SessionModel.started_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return {"items": [_to_session(r) for r in items], "total": total}
    finally:
        db.close()


# --- Utterances ---


def create_utterance(session_id: str, **kwargs) -> Dict:
    db = SessionLocal()
    try:
        utterance = UtteranceModel(session_id=session_id, **kwargs)
        db.add(utterance)
        db.commit()
        db.refresh(utterance)
        return _to_utterance(utterance)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_utterance(utterance_id: str) -> Optional[Dict]:
    db = SessionLocal()
    try:
        row = db.query(UtteranceModel).filter(UtteranceModel.id == utterance_id).first()
        return _to_utterance(row) if row else None
    finally:
        db.close()


def list_utterances(session_id: str, limit: int = 200) -> List[Dict]:
    db = SessionLocal()
    try:
        rows = (
            db.query(UtteranceModel)
            .filter(UtteranceModel.session_id == session_id)
            .order_by(UtteranceModel.created_at.asc())
            .limit(limit)
            .all()
        )
        return [_to_utterance(r) for r in rows]
    finally:
        db.close()


# --- Weak Points ---


def upsert_weak_point(phrase: str, session_id: Optional[str] = None, **kwargs) -> Dict:
    """Update count if the phrase already exists, otherwise insert."""
    last_seen = kwargs.pop("last_seen_at", datetime.now(timezone.utc))
    issue_type = kwargs.pop("issue_type", None)
    db = SessionLocal()
    try:
        point = (
            db.query(WeakPointModel)
            .filter(WeakPointModel.phrase == phrase)
            .first()
        )
        if point:
            point.count += 1
            point.last_seen_at = last_seen
        else:
            # Build extra fields without double-passing known params
            extra: Dict[str, Any] = {
                "phrase": phrase,
                "session_id": session_id,
                "count": 1,
                "last_seen_at": last_seen,
            }
            if issue_type:
                extra["issue_type"] = issue_type
            extra.update(kwargs)
            point = WeakPointModel(**extra)
            db.add(point)
        db.commit()
        db.refresh(point)
        return _to_weak_point(point)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def list_weak_points(limit: int = 50) -> List[Dict]:
    db = SessionLocal()
    try:
        rows = (
            db.query(WeakPointModel)
            .order_by(WeakPointModel.count.desc(), WeakPointModel.last_seen_at.desc())
            .limit(limit)
            .all()
        )
        return [_to_weak_point(r) for r in rows]
    finally:
        db.close()


def pick_next_review() -> Optional[Dict]:
    """Pick one weak point to review (lowest count first, then newest)."""
    db = SessionLocal()
    try:
        row = (
            db.query(WeakPointModel)
            .order_by(WeakPointModel.count.asc(), WeakPointModel.last_seen_at.desc())
            .first()
        )
        return _to_weak_point(row) if row else None
    finally:
        db.close()


# --- Session helpers ---


def complete_session(session_id: str) -> None:
    """Mark a session's ``ended_at`` timestamp (called when the session ends)."""
    db = SessionLocal()
    try:
        db.query(SessionModel).filter(SessionModel.id == session_id).update(
            {SessionModel.ended_at: datetime.now(timezone.utc)},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Singleton for import convenience
db_repo = type("DbRepo", (), {k: v for k, v in locals().items() if callable(v) and not k.startswith("_")})()
