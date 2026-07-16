from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import get_settings
from .base import Base
from . import models  # noqa: F401

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _configure_sqlite(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_engine(force_refresh: bool = False) -> Engine:
    global _engine, _SessionLocal
    if _engine is not None and not force_refresh:
        return _engine

    settings = get_settings()
    url = settings.resolved_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    _engine = create_engine(url, future=True, pool_pre_ping=True, connect_args=connect_args)
    if url.startswith("sqlite"):
        _configure_sqlite(_engine)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


@contextmanager
def session_scope() -> Iterator[Session]:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create schema for current engine (SQLite default or Postgres via DATABASE_URL)."""
    get_settings.cache_clear()
    engine = get_engine(force_refresh=True)
    Base.metadata.create_all(bind=engine)
    # Soft migrations for existing SQLite files created before Phase 1 columns.
    if str(engine.url).startswith("sqlite"):
        with engine.begin() as conn:
            cols = {row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()}
            alters = []
            if "password_hash" not in cols:
                alters.append("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)")
            if "failed_login_count" not in cols:
                alters.append("ALTER TABLE users ADD COLUMN failed_login_count INTEGER DEFAULT 0")
            if "locked_until" not in cols:
                alters.append("ALTER TABLE users ADD COLUMN locked_until VARCHAR(64)")
            if "is_active" not in cols:
                alters.append("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
            for stmt in alters:
                conn.execute(text(stmt))


def reset_engine() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
    get_settings.cache_clear()
