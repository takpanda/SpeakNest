"""SQLAlchemy ORM models for SpeakNest.

Tables
------
sessions        – each learning session (conversation or shadowing)
utterances      – individual utterances inside a session
weak_points     – auto-extracted weak phrases
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


def _uuid() -> str:
    return str(uuid.uuid4())


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Text, primary_key=True, default=_uuid)
    mode = Column(Text, nullable=False, default="conversation")  # conversation | shadowing
    scenario = Column(Text, nullable=True)
    level = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    utterances = relationship("Utterance", back_populates="session", cascade="all, delete-orphan")
    weak_points = relationship("WeakPoint", back_populates="session", cascade="all, delete-orphan")

    def as_dict(self):
        return {
            "id": self.id,
            "mode": self.mode,
            "scenario": self.scenario,
            "level": self.level,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }


class Utterance(Base):
    __tablename__ = "utterances"

    id = Column(Text, primary_key=True, default=_uuid)
    session_id = Column(Text, ForeignKey("sessions.id"), nullable=False)
    role = Column(Text, nullable=True)  # user | assistant
    audio_path = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    target_text = Column(Text, nullable=True)
    wer = Column(Float, nullable=True)
    score = Column(Integer, nullable=True)
    feedback_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    session = relationship("Session", back_populates="utterances")

    def as_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "audio_path": self.audio_path,
            "transcript": self.transcript,
            "target_text": self.target_text,
            "wer": self.wer,
            "score": self.score,
            "feedback_json": self.feedback_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WeakPoint(Base):
    __tablename__ = "weak_points"
    __table_args__ = (
        Index("ix_weak_points_phrase", "phrase"),
    )

    id = Column(Text, primary_key=True, default=_uuid)
    session_id = Column(Text, ForeignKey("sessions.id"), nullable=True)
    user_id = Column(Text, nullable=True)  # reserved for Phase 3+
    phrase = Column(Text, nullable=False)
    issue_type = Column(Text, nullable=True)  # missing | misrecognized | slow
    count = Column(Integer, nullable=False, default=1)
    last_seen_at = Column(DateTime, nullable=True)

    session = relationship("Session", back_populates="weak_points")

    def as_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "phrase": self.phrase,
            "issue_type": self.issue_type,
            "count": self.count,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
        }
