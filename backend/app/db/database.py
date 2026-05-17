from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session as SASession, sessionmaker

from app.config import DB_FILE_PATH
from app.db.models import Base


def _resolve_db_url() -> str:
    path = DB_FILE_PATH
    # When the parent dir doesn't exist (e.g. non-Docker local dev),
    # fall back to a writable temp directory.
    if not path.parent.exists():
        fallback = Path("/tmp") / "speaknest.db"
        path = fallback
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"


DATABASE_URL = _resolve_db_url()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def enable_fk(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db_and_tables() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> SASession:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
