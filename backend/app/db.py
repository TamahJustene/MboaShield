from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .config import ROOT

DEFAULT_DB_PATH = ROOT / "storage" / "mboashield.db"


def get_db_path() -> Path:
    raw = os.getenv("MBOASHIELD_DB_PATH", "").strip()
    return Path(raw) if raw else DEFAULT_DB_PATH


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    db_path = get_db_path()
    _ensure_parent_dir(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS verification_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_type TEXT NOT NULL,
                input_text TEXT,
                input_handle TEXT,
                input_filename TEXT,
                input_lang TEXT NOT NULL DEFAULT 'en',
                risk_score INTEGER,
                risk_band TEXT,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS lesson_certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                certificate_id TEXT NOT NULL UNIQUE,
                learner_name TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                lesson_title_en TEXT NOT NULL,
                lesson_title_fr TEXT NOT NULL,
                issued_on TEXT NOT NULL,
                issuer TEXT NOT NULL,
                founder TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS verification_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verification_check_id INTEGER NOT NULL,
                signal_type TEXT NOT NULL,
                signal_label TEXT NOT NULL,
                signal_score INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (verification_check_id) REFERENCES verification_checks(id)
            );

            CREATE TABLE IF NOT EXISTS institutions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                short_name TEXT NOT NULL,
                website_url TEXT,
                verified INTEGER NOT NULL DEFAULT 1,
                handles_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,
                email TEXT,
                role TEXT NOT NULL DEFAULT 'citizen',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS incident_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verification_check_id INTEGER,
                user_id INTEGER,
                report_type TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                reviewer_note TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (verification_check_id) REFERENCES verification_checks(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )
        try:
            conn.execute("ALTER TABLE verification_checks ADD COLUMN user_id INTEGER")
        except sqlite3.OperationalError:
            pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

