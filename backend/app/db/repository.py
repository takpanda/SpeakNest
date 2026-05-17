from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import Session as SessionModel
from app.db.models import Utterance, WeakPoint


# ===== sessions CRUD =====


def create_session(
    db: Session,
    *,
    mode: str,
    scenario: Optional[str] = None,
    level: Optional[str] = None,
    started_at: Optional[datetime] = None,
) -> SessionModel:
    now = datetime.now(timezone.utc)
    db_session = SessionModel(
        id=str(uuid.uuid4()),
        mode=mode,
        scenario=scenario,
        level=level,
        started_at=started_at or now,
        ended_at=None,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_session(db: Session, session_id: str) -> Optional[SessionModel]:
    return db.query(SessionModel).filter(SessionModel.id == session_id).first()


def list_sessions(
    db: Session,
    *,
    mode: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[SessionModel]:
    query = db.query(SessionModel)
    if mode:
        query = query.filter(SessionModel.mode == mode)
    return query.order_by(SessionModel.started_at.desc()).offset(offset).limit(limit).all()


def end_session(
    db: Session, session_id: str, ended_at: Optional[datetime] = None
) -> Optional[SessionModel]:
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if db_session:
        db_session.ended_at = ended_at or datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_session)
    return db_session


# ===== utterances CRUD =====


def create_utterance(
    db: Session,
    *,
    session_id: str,
    role: str,
    audio_path: Optional[str] = None,
    transcript: Optional[str] = None,
    target_text: Optional[str] = None,
    wer: Optional[float] = None,
    score: Optional[int] = None,
    feedback_json: Optional[str] = None,
    created_at: Optional[datetime] = None,
) -> Utterance:
    now = datetime.now(timezone.utc)
    utt = Utterance(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role=role,
        audio_path=audio_path,
        transcript=transcript,
        target_text=target_text,
        wer=wer,
        score=score,
        feedback_json=feedback_json,
        created_at=created_at or now,
    )
    db.add(utt)
    db.commit()
    db.refresh(utt)
    return utt


def get_utterance(db: Session, utterance_id: str) -> Optional[Utterance]:
    return db.query(Utterance).filter(Utterance.id == utterance_id).first()


def list_utterances(
    db: Session,
    session_id: str,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[Utterance]:
    return (
        db.query(Utterance)
        .filter(Utterance.session_id == session_id)
        .order_by(Utterance.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def delete_utterance(db: Session, utterance_id: str) -> bool:
    utt = db.query(Utterance).filter(Utterance.id == utterance_id).first()
    if utt:
        db.delete(utt)
        db.commit()
        return True
    return False


# ===== weak_points CRUD =====


def upsert_weak_point(
    db: Session,
    *,
    phrase: str,
    issue_type: str,
) -> WeakPoint:
    existing = (
        db.query(WeakPoint)
        .filter(WeakPoint.phrase == phrase)
        .first()
    )
    if existing:
        existing.count += 1
        existing.last_seen_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    wp = WeakPoint(
        id=str(uuid.uuid4()),
        phrase=phrase,
        issue_type=issue_type,
        count=1,
        last_seen_at=datetime.now(timezone.utc),
    )
    db.add(wp)
    db.commit()
    db.refresh(wp)
    return wp


def get_weak_points(
    db: Session,
    *,
    issue_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[WeakPoint]:
    query = db.query(WeakPoint)
    if issue_type:
        query = query.filter(WeakPoint.issue_type == issue_type)
    return query.order_by(WeakPoint.count.desc()).offset(offset).limit(limit).all()


def get_weak_point(db: Session, wp_id: str) -> Optional[WeakPoint]:
    return db.query(WeakPoint).filter(WeakPoint.id == wp_id).first()
