"""SQLAlchemy database engine and session management for SpeakNest.

Tables are created eagerly on import so tests and the app work even when
``on_event("startup")`` does not fire (e.g. TestClient).
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

DB_URL = settings.database_url if hasattr(settings, "database_url") and settings.database_url else "sqlite:///./data/speaknest.db"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables defined in models. Idempotent (no-op if tables exist)."""
    from app.db.models import Base  # noqa: local import to avoid circular
    Base.metadata.create_all(bind=engine)


# Eager init so tests and the app work without relying on startup events.
init_db()


def get_db():
    """Yield a database session; close on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
