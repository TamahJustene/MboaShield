"""Persistence layer - SQLAlchemy backed, SQLite by default, PostgreSQL via DATABASE_URL.

Public function signatures are stable for existing API routes and tests.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from .core.security import hash_password, verify_password
from .db.models import (
    AuditLog,
    IncidentReport,
    Institution,
    LessonCertificate,
    RefreshToken,
    User,
    VerificationCheck,
    VerificationSignal,
)
from .db.session import session_scope


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


ALLOWED_REPORT_TYPES = {
    "disinformation",
    "impersonation",
    "voice_clone",
    "synthetic_media",
    "scam",
    "other",
}

ALLOWED_REPORT_STATUSES = {"open", "reviewing", "resolved", "dismissed"}


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


def _row_to_check(check: VerificationCheck, signals: list[dict[str, Any]] | None = None) -> dict:
    return {
        "id": check.id,
        "check_type": check.check_type,
        "input": {
            "text": check.input_text,
            "handle": check.input_handle,
            "filename": check.input_filename,
            "lang": check.input_lang,
        },
        "risk_score": check.risk_score,
        "risk_band": check.risk_band,
        "result": json.loads(check.result_json),
        "signals": signals or [],
        "created_at": check.created_at,
    }


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
    stamp = now_iso()
    with session_scope() as session:
        check = VerificationCheck(
            check_type=check_type,
            input_text=input_text,
            input_handle=input_handle,
            input_filename=input_filename,
            input_lang=lang,
            risk_score=result.get("risk_score"),
            risk_band=result.get("risk_band"),
            result_json=json.dumps(result, ensure_ascii=True),
            created_at=stamp,
            user_id=user_id,
        )
        session.add(check)
        session.flush()
        for signal in signals:
            session.add(
                VerificationSignal(
                    verification_check_id=check.id,
                    signal_type=signal["signal_type"],
                    signal_label=signal["signal_label"],
                    signal_score=signal.get("signal_score"),
                    created_at=stamp,
                )
            )
        session.flush()
        return int(check.id)


def get_verification_check(check_id: int) -> dict | None:
    with session_scope() as session:
        check = session.get(VerificationCheck, check_id)
        if not check:
            return None
        signal_rows = session.scalars(
            select(VerificationSignal)
            .where(VerificationSignal.verification_check_id == check_id)
            .order_by(VerificationSignal.id.asc())
        ).all()
        signals = [
            {
                "signal_type": row.signal_type,
                "signal_label": row.signal_label,
                "signal_score": row.signal_score,
            }
            for row in signal_rows
        ]
        return _row_to_check(check, signals)


def list_recent_verification_checks(limit: int = 20, check_type: str | None = None) -> list[dict]:
    safe_limit = max(1, min(limit, 100))
    with session_scope() as session:
        stmt = select(VerificationCheck).order_by(VerificationCheck.id.desc()).limit(safe_limit)
        if check_type:
            stmt = (
                select(VerificationCheck)
                .where(VerificationCheck.check_type == check_type)
                .order_by(VerificationCheck.id.desc())
                .limit(safe_limit)
            )
        checks = session.scalars(stmt).all()
        items = []
        for check in checks:
            signal_rows = session.scalars(
                select(VerificationSignal)
                .where(VerificationSignal.verification_check_id == check.id)
                .order_by(VerificationSignal.id.asc())
            ).all()
            signals = [
                {
                    "signal_type": row.signal_type,
                    "signal_label": row.signal_label,
                    "signal_score": row.signal_score,
                }
                for row in signal_rows
            ]
            items.append(_row_to_check(check, signals))
        return items


def save_certificate(certificate: dict) -> int:
    with session_scope() as session:
        row = LessonCertificate(
            certificate_id=certificate["id"],
            learner_name=certificate["learner_name"],
            lesson_id=certificate["lesson_id"],
            lesson_title_en=certificate["lesson_title_en"],
            lesson_title_fr=certificate["lesson_title_fr"],
            issued_on=certificate["issued_on"],
            issuer=certificate["issuer"],
            founder=certificate["founder"],
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        return int(row.id)


def _row_to_certificate(row: LessonCertificate) -> dict:
    return {
        "id": row.id,
        "certificate_id": row.certificate_id,
        "learner_name": row.learner_name,
        "lesson_id": row.lesson_id,
        "lesson_title_en": row.lesson_title_en,
        "lesson_title_fr": row.lesson_title_fr,
        "issued_on": row.issued_on,
        "issuer": row.issuer,
        "founder": row.founder,
        "created_at": row.created_at,
    }


def get_certificate(certificate_id: str) -> dict | None:
    with session_scope() as session:
        row = session.scalar(select(LessonCertificate).where(LessonCertificate.certificate_id == certificate_id))
        if not row:
            return None
        return _row_to_certificate(row)


def list_recent_certificates(limit: int = 20) -> list[dict]:
    safe_limit = max(1, min(limit, 100))
    with session_scope() as session:
        rows = session.scalars(
            select(LessonCertificate).order_by(LessonCertificate.id.desc()).limit(safe_limit)
        ).all()
        return [_row_to_certificate(row) for row in rows]


def _row_to_institution(row: Institution) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "short_name": row.short_name,
        "url": row.website_url,
        "verified": bool(row.verified),
        "handles": json.loads(row.handles_json or "[]"),
        "created_at": row.created_at,
    }


def list_institutions() -> list[dict]:
    with session_scope() as session:
        rows = session.scalars(select(Institution).order_by(Institution.short_name.asc())).all()
        return [_row_to_institution(row) for row in rows]


def get_institution(institution_id: str) -> dict | None:
    with session_scope() as session:
        row = session.get(Institution, institution_id)
        if not row:
            return None
        return _row_to_institution(row)


def _user_to_dict(row: User) -> dict:
    return {
        "id": row.id,
        "display_name": row.display_name,
        "email": row.email,
        "role": row.role,
        "created_at": row.created_at,
        "is_active": bool(row.is_active),
    }


def create_user(
    *,
    display_name: str,
    email: str | None = None,
    role: str = "citizen",
    password: str | None = None,
) -> dict:
    name = display_name.strip()
    if not name:
        raise ValueError("display_name is required")
    with session_scope() as session:
        row = User(
            display_name=name,
            email=(email or "").strip() or None,
            role=role,
            password_hash=hash_password(password) if password else None,
            failed_login_count=0,
            locked_until=None,
            is_active=True,
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        return _user_to_dict(row)


def get_user(user_id: int) -> dict | None:
    with session_scope() as session:
        row = session.get(User, user_id)
        if not row:
            return None
        return _user_to_dict(row)


def get_user_by_email(email: str) -> dict | None:
    cleaned = (email or "").strip()
    if not cleaned:
        return None
    with session_scope() as session:
        row = session.scalar(select(User).where(User.email == cleaned))
        if not row:
            row = session.scalar(select(User).where(User.email == cleaned.lower()))
        if not row:
            return None
        return _user_to_dict(row)


def authenticate_user(email: str, password: str) -> dict | None:
    cleaned = (email or "").strip()
    with session_scope() as session:
        row = session.scalar(select(User).where(User.email == cleaned))
        if not row:
            row = session.scalar(select(User).where(User.email == cleaned.lower()))
        if not row or not row.is_active:
            return None

        if row.locked_until:
            try:
                locked = datetime.fromisoformat(row.locked_until)
                if locked.tzinfo is None:
                    locked = locked.replace(tzinfo=timezone.utc)
                if locked > datetime.now(timezone.utc):
                    raise ValueError("Account temporarily locked due to failed login attempts")
            except ValueError as exc:
                if "Account temporarily locked" in str(exc):
                    raise

        if not verify_password(password, row.password_hash):
            from datetime import timedelta

            row.failed_login_count = int(row.failed_login_count or 0) + 1
            if row.failed_login_count >= 5:
                row.locked_until = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
            return None

        row.failed_login_count = 0
        row.locked_until = None
        return _user_to_dict(row)


def store_refresh_token(user_id: int, raw_token: str, expires_at: str) -> None:
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    with session_scope() as session:
        session.add(
            RefreshToken(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
                revoked=False,
                created_at=now_iso(),
            )
        )


def revoke_refresh_token(raw_token: str) -> bool:
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    with session_scope() as session:
        row = session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        if not row:
            return False
        row.revoked = True
        return True


def get_valid_refresh_token(raw_token: str) -> dict | None:
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    with session_scope() as session:
        row = session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        if not row or row.revoked:
            return None
        try:
            expires = datetime.fromisoformat(row.expires_at)
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < datetime.now(timezone.utc):
                return None
        except ValueError:
            return None
        return {"id": row.id, "user_id": row.user_id, "expires_at": row.expires_at}


def _row_to_incident(row: IncidentReport) -> dict:
    return {
        "id": row.id,
        "verification_check_id": row.verification_check_id,
        "user_id": row.user_id,
        "report_type": row.report_type,
        "description": row.description,
        "status": row.status,
        "reviewer_note": row.reviewer_note,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
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
    with session_scope() as session:
        row = IncidentReport(
            verification_check_id=verification_check_id,
            user_id=user_id,
            report_type=report_type,
            description=description,
            status="open",
            reviewer_note=None,
            created_at=stamp,
            updated_at=stamp,
        )
        session.add(row)
        session.flush()
        return _row_to_incident(row)


def get_incident_report(report_id: int) -> dict | None:
    with session_scope() as session:
        row = session.get(IncidentReport, report_id)
        if not row:
            return None
        return _row_to_incident(row)


def list_incident_reports(limit: int = 20, status: str | None = None) -> list[dict]:
    safe_limit = max(1, min(limit, 100))
    with session_scope() as session:
        stmt = select(IncidentReport).order_by(IncidentReport.id.desc()).limit(safe_limit)
        if status:
            if status not in ALLOWED_REPORT_STATUSES:
                raise ValueError(f"Invalid status. Allowed: {', '.join(sorted(ALLOWED_REPORT_STATUSES))}")
            stmt = (
                select(IncidentReport)
                .where(IncidentReport.status == status)
                .order_by(IncidentReport.id.desc())
                .limit(safe_limit)
            )
        rows = session.scalars(stmt).all()
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
    with session_scope() as session:
        row = session.get(IncidentReport, report_id)
        if not row:
            return None
        row.status = status
        if reviewer_note is not None:
            row.reviewer_note = reviewer_note
        row.updated_at = now_iso()
        session.flush()
        return _row_to_incident(row)


def write_audit_log(
    *,
    action: str,
    outcome: str = "success",
    actor_user_id: int | None = None,
    actor_role: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict | None = None,
) -> int:
    with session_scope() as session:
        row = AuditLog(
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json=json.dumps(details or {}, ensure_ascii=True),
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        return int(row.id)


def list_audit_logs(limit: int = 50) -> list[dict]:
    safe_limit = max(1, min(limit, 200))
    with session_scope() as session:
        rows = session.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(safe_limit)).all()
        return [
            {
                "id": row.id,
                "actor_user_id": row.actor_user_id,
                "actor_role": row.actor_role,
                "action": row.action,
                "resource_type": row.resource_type,
                "resource_id": row.resource_id,
                "outcome": row.outcome,
                "ip_address": row.ip_address,
                "created_at": row.created_at,
                "details": json.loads(row.details_json or "{}"),
            }
            for row in rows
        ]
