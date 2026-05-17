from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# ======================== sessions ========================


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Text, primary_key=True)
    mode = Column(Text, nullable=False)
    scenario = Column(Text, nullable=True)
    level = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Session id={self.id} mode={self.mode}>"


# ======================== utterances ========================


class Utterance(Base):
    __tablename__ = "utterances"

    id = Column(Text, primary_key=True)
    session_id = Column(Text, nullable=False)
    role = Column(Text, nullable=False)
    audio_path = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    target_text = Column(Text, nullable=True)
    wer = Column(Float, nullable=True)
    score = Column(Integer, nullable=True)
    feedback_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return f"<Utterance id={self.id} session_id={self.session_id} role={self.role}>"


# ======================== weak_points ========================


class WeakPoint(Base):
    __tablename__ = "weak_points"

    id = Column(Text, primary_key=True)
    phrase = Column(Text, nullable=False)
    issue_type = Column(Text, nullable=False)
    count = Column(Integer, nullable=False)
    last_seen_at = Column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return f"<WeakPoint id={self.id} phrase={self.phrase} issue_type={self.issue_type}>"
