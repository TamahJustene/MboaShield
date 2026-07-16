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
    if str(engine.url).startswith("sqlite"):
        with engine.begin() as conn:
            user_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()}
            for stmt in [
                ("password_hash", "ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"),
                ("failed_login_count", "ALTER TABLE users ADD COLUMN failed_login_count INTEGER DEFAULT 0"),
                ("locked_until", "ALTER TABLE users ADD COLUMN locked_until VARCHAR(64)"),
                ("is_active", "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"),
                ("mfa_enabled", "ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT 0"),
                ("mfa_secret", "ALTER TABLE users ADD COLUMN mfa_secret VARCHAR(255)"),
                ("oidc_subject", "ALTER TABLE users ADD COLUMN oidc_subject VARCHAR(255)"),
                ("oidc_provider", "ALTER TABLE users ADD COLUMN oidc_provider VARCHAR(64)"),
                ("auth_provider", "ALTER TABLE users ADD COLUMN auth_provider VARCHAR(32) DEFAULT 'local'"),
                ("must_reset_password", "ALTER TABLE users ADD COLUMN must_reset_password BOOLEAN DEFAULT 0"),
                ("invited_by_user_id", "ALTER TABLE users ADD COLUMN invited_by_user_id INTEGER"),
                ("last_login_at", "ALTER TABLE users ADD COLUMN last_login_at VARCHAR(64)"),
            ]:
                if stmt[0] not in user_cols:
                    conn.execute(text(stmt[1]))

            incident_cols = {
                row[1] for row in conn.execute(text("PRAGMA table_info(incident_reports)")).fetchall()
            }
            for col, ddl in [
                ("priority", "ALTER TABLE incident_reports ADD COLUMN priority VARCHAR(32) DEFAULT 'normal'"),
                ("region", "ALTER TABLE incident_reports ADD COLUMN region VARCHAR(128)"),
                ("assigned_to_user_id", "ALTER TABLE incident_reports ADD COLUMN assigned_to_user_id INTEGER"),
                ("institution_id", "ALTER TABLE incident_reports ADD COLUMN institution_id VARCHAR(64)"),
                ("decision_summary", "ALTER TABLE incident_reports ADD COLUMN decision_summary TEXT"),
                ("public_advisory", "ALTER TABLE incident_reports ADD COLUMN public_advisory TEXT"),
                ("ai_summary_json", "ALTER TABLE incident_reports ADD COLUMN ai_summary_json TEXT"),
            ]:
                if col not in incident_cols:
                    conn.execute(text(ddl))


def reset_engine() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
    get_settings.cache_clear()
