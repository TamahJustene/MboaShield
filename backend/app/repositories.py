from __future__ import annotations

import json
from typing import Any

from .db import get_conn, now_iso


def _extract_signals(result: dict) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []

    for reason in result.get("reasons", []):
        signals.append({"signal_type": "reason", "signal_label": str(reason), "signal_score": None})

    source = result.get("source_verification") or {}
    for scam in source.get("scam_signals", []):
        signals.append({"signal_type": "scam_signal", "signal_label": str(scam), "signal_score": None})

    matched = result.get("matched_institution")
    if matched:
        label = f"{matched.get('short_name', '')} ({matched.get('name', '')})".strip()
        signals.append({"signal_type": "institution_match", "signal_label": label, "signal_score": None})

    if result.get("is_suspicious"):
        signals.append(
            {
                "signal_type": "impersonation_flag",
                "signal_label": "Account marked suspicious",
                "signal_score": result.get("risk_score"),
            }
        )

    analysis = result.get("ai_analysis") or {}
    for threat in analysis.get("threat_categories", []):
        signals.append(
            {
                "signal_type": "threat_category",
                "signal_label": str(threat),
                "signal_score": analysis.get("confidence"),
            }
        )
    if analysis.get("confidence") is not None:
        signals.append(
            {
                "signal_type": "ai_confidence",
                "signal_label": f"AI confidence {analysis.get('confidence')}/100",
                "signal_score": analysis.get("confidence"),
            }
        )

    return signals[:20]


def _save_signals(conn, check_id: int, signals: list[dict[str, Any]]) -> None:
    for signal in signals:
        conn.execute(
            """
            INSERT INTO verification_signals (
                verification_check_id,
                signal_type,
                signal_label,
                signal_score,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                check_id,
                signal["signal_type"],
                signal["signal_label"],
                signal.get("signal_score"),
                now_iso(),
            ),
        )


def _row_to_check(row, signals: list[dict[str, Any]] | None = None) -> dict:
    return {
        "id": row["id"],
        "check_type": row["check_type"],
        "input": {
            "text": row["input_text"],
            "handle": row["input_handle"],
            "filename": row["input_filename"],
            "lang": row["input_lang"],
        },
        "risk_score": row["risk_score"],
        "risk_band": row["risk_band"],
        "result": json.loads(row["result_json"]),
        "signals": signals or [],
        "created_at": row["created_at"],
    }


def _load_signals_for_check(conn, check_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT signal_type, signal_label, signal_score
        FROM verification_signals
        WHERE verification_check_id = ?
        ORDER BY id ASC
        """,
        (check_id,),
    ).fetchall()
    return [
        {
            "signal_type": row["signal_type"],
            "signal_label": row["signal_label"],
            "signal_score": row["signal_score"],
        }
        for row in rows
    ]


def save_verification_check(
    *,
    check_type: str,
    result: dict,
    lang: str = "en",
    input_text: str = "",
    input_handle: str = "",
    input_filename: str = "",
    user_id: int | None = None,
) -> int:
    signals = _extract_signals(result)
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO verification_checks (
                check_type,
                input_text,
                input_handle,
                input_filename,
                input_lang,
                risk_score,
                risk_band,
                result_json,
                created_at,
                user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                check_type,
                input_text,
                input_handle,
                input_filename,
                lang,
                result.get("risk_score"),
                result.get("risk_band"),
                json.dumps(result, ensure_ascii=True),
                now_iso(),
                user_id,
            ),
        )
        check_id = int(cur.lastrowid)
        _save_signals(conn, check_id, signals)
        return check_id


def get_verification_check(check_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT
                id,
                check_type,
                input_text,
                input_handle,
                input_filename,
                input_lang,
                risk_score,
                risk_band,
                result_json,
                created_at
            FROM verification_checks
            WHERE id = ?
            """,
            (check_id,),
        ).fetchone()
        if not row:
            return None
        signals = _load_signals_for_check(conn, check_id)
        return _row_to_check(row, signals)


def list_recent_verification_checks(limit: int = 20, check_type: str | None = None) -> list[dict]:
    safe_limit = max(1, min(limit, 100))
    query = """
        SELECT
            id,
            check_type,
            input_text,
            input_handle,
            input_filename,
            input_lang,
            risk_score,
            risk_band,
            result_json,
            created_at
        FROM verification_checks
    """
    params: list[object] = []
    if check_type:
        query += " WHERE check_type = ?"
        params.append(check_type)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(safe_limit)

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        items = []
        for row in rows:
            signals = _load_signals_for_check(conn, row["id"])
            items.append(_row_to_check(row, signals))
        return items


def save_certificate(certificate: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO lesson_certificates (
                certificate_id,
                learner_name,
                lesson_id,
                lesson_title_en,
                lesson_title_fr,
                issued_on,
                issuer,
                founder,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                certificate["id"],
                certificate["learner_name"],
                certificate["lesson_id"],
                certificate["lesson_title_en"],
                certificate["lesson_title_fr"],
                certificate["issued_on"],
                certificate["issuer"],
                certificate["founder"],
                now_iso(),
            ),
        )
        return int(cur.lastrowid)


def _row_to_certificate(row) -> dict:
    return {
        "id": row["id"],
        "certificate_id": row["certificate_id"],
        "learner_name": row["learner_name"],
        "lesson_id": row["lesson_id"],
        "lesson_title_en": row["lesson_title_en"],
        "lesson_title_fr": row["lesson_title_fr"],
        "issued_on": row["issued_on"],
        "issuer": row["issuer"],
        "founder": row["founder"],
        "created_at": row["created_at"],
    }


def get_certificate(certificate_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT
                id,
                certificate_id,
                learner_name,
                lesson_id,
                lesson_title_en,
                lesson_title_fr,
                issued_on,
                issuer,
                founder,
                created_at
            FROM lesson_certificates
            WHERE certificate_id = ?
            """,
            (certificate_id,),
        ).fetchone()
        if not row:
            return None
        return _row_to_certificate(row)


def list_recent_certificates(limit: int = 20) -> list[dict]:
    safe_limit = max(1, min(limit, 100))
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                certificate_id,
                learner_name,
                lesson_id,
                lesson_title_en,
                lesson_title_fr,
                issued_on,
                issuer,
                founder,
                created_at
            FROM lesson_certificates
            ORDER BY id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()
        return [_row_to_certificate(row) for row in rows]


def _row_to_institution(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "short_name": row["short_name"],
        "url": row["website_url"],
        "verified": bool(row["verified"]),
        "handles": json.loads(row["handles_json"] or "[]"),
        "created_at": row["created_at"],
    }


def list_institutions() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, name, short_name, website_url, verified, handles_json, created_at
            FROM institutions
            ORDER BY short_name ASC
            """
        ).fetchall()
        return [_row_to_institution(row) for row in rows]


def get_institution(institution_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, name, short_name, website_url, verified, handles_json, created_at
            FROM institutions
            WHERE id = ?
            """,
            (institution_id,),
        ).fetchone()
        if not row:
            return None
        return _row_to_institution(row)


def create_user(*, display_name: str, email: str | None = None, role: str = "citizen") -> dict:
    name = display_name.strip()
    if not name:
        raise ValueError("display_name is required")
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO users (display_name, email, role, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (name, (email or "").strip() or None, role, now_iso()),
        )
        user_id = int(cur.lastrowid)
        row = conn.execute(
            "SELECT id, display_name, email, role, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return {
            "id": row["id"],
            "display_name": row["display_name"],
            "email": row["email"],
            "role": row["role"],
            "created_at": row["created_at"],
        }


def get_user(user_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, display_name, email, role, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "display_name": row["display_name"],
            "email": row["email"],
            "role": row["role"],
            "created_at": row["created_at"],
        }


ALLOWED_REPORT_TYPES = {
    "disinformation",
    "impersonation",
    "voice_clone",
    "synthetic_media",
    "scam",
    "other",
}

ALLOWED_REPORT_STATUSES = {"open", "reviewing", "resolved", "dismissed"}


def _row_to_incident(row) -> dict:
    return {
        "id": row["id"],
        "verification_check_id": row["verification_check_id"],
        "user_id": row["user_id"],
        "report_type": row["report_type"],
        "description": row["description"],
        "status": row["status"],
        "reviewer_note": row["reviewer_note"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def create_incident_report(
    *,
    report_type: str,
    description: str,
    verification_check_id: int | None = None,
    user_id: int | None = None,
) -> dict:
    report_type = (report_type or "").strip().lower()
    description = (description or "").strip()
    if report_type not in ALLOWED_REPORT_TYPES:
        raise ValueError(f"Invalid report_type. Allowed: {', '.join(sorted(ALLOWED_REPORT_TYPES))}")
    if len(description) < 8:
        raise ValueError("description must be at least 8 characters")

    if verification_check_id is not None and not get_verification_check(verification_check_id):
        raise ValueError("verification_check_id not found")
    if user_id is not None and not get_user(user_id):
        raise ValueError("user_id not found")

    stamp = now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO incident_reports (
                verification_check_id,
                user_id,
                report_type,
                description,
                status,
                reviewer_note,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, 'open', NULL, ?, ?)
            """,
            (verification_check_id, user_id, report_type, description, stamp, stamp),
        )
        report_id = int(cur.lastrowid)
        row = conn.execute(
            """
            SELECT id, verification_check_id, user_id, report_type, description,
                   status, reviewer_note, created_at, updated_at
            FROM incident_reports
            WHERE id = ?
            """,
            (report_id,),
        ).fetchone()
        return _row_to_incident(row)


def get_incident_report(report_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, verification_check_id, user_id, report_type, description,
                   status, reviewer_note, created_at, updated_at
            FROM incident_reports
            WHERE id = ?
            """,
            (report_id,),
        ).fetchone()
        if not row:
            return None
        return _row_to_incident(row)


def list_incident_reports(limit: int = 20, status: str | None = None) -> list[dict]:
    safe_limit = max(1, min(limit, 100))
    query = """
        SELECT id, verification_check_id, user_id, report_type, description,
               status, reviewer_note, created_at, updated_at
        FROM incident_reports
    """
    params: list[object] = []
    if status:
        if status not in ALLOWED_REPORT_STATUSES:
            raise ValueError(f"Invalid status. Allowed: {', '.join(sorted(ALLOWED_REPORT_STATUSES))}")
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(safe_limit)

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [_row_to_incident(row) for row in rows]


def update_incident_status(
    report_id: int,
    *,
    status: str,
    reviewer_note: str | None = None,
) -> dict | None:
    status = (status or "").strip().lower()
    if status not in ALLOWED_REPORT_STATUSES:
        raise ValueError(f"Invalid status. Allowed: {', '.join(sorted(ALLOWED_REPORT_STATUSES))}")

    existing = get_incident_report(report_id)
    if not existing:
        return None

    note = reviewer_note if reviewer_note is not None else existing.get("reviewer_note")
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE incident_reports
            SET status = ?, reviewer_note = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, note, now_iso(), report_id),
        )
    return get_incident_report(report_id)
