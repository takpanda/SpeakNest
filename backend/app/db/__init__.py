"""SpeakNest SQLite database models and engine.

This package exports:
- ``Base`` – SQLAlchemy declarative base (import from ``models``)
- ``engine`` – sync SQLAlchemy engine (import from ``database``)
- ``SessionLocal`` – session factory (import from ``database``)
- ``Session, Utterance, WeakPoint`` – ORM model classes
- ``db_repo`` – CRUD repository instance
"""

from app.db.database import engine, SessionLocal, init_db  # noqa: F401
from app.db.models import Base, Session, Utterance, WeakPoint  # noqa: F401
from app.db.repository import db_repo  # noqa: F401

# Ensure Base is importable for ``init_db`` callers that rely on ``Base.metadata.create_all``.
__all__ = ["Base", "Session", "Utterance", "WeakPoint", "engine", "SessionLocal", "init_db", "db_repo"]
