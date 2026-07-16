"""Persistence layer - SQLAlchemy backed, SQLite by default, PostgreSQL via DATABASE_URL.

Public function signatures are stable for existing API routes and tests.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from .core.security import generate_api_key, hash_api_key, hash_password, verify_password
from .db.models import (
    AuditLog,
    IncidentEvent,
    IncidentReport,
    Institution,
    LessonCertificate,
    PartnerApiKey,
    RefreshToken,
    User,
    VerificationCheck,
    VerificationSignal,
)
from .db.session import session_scope
from .services.incident_workflow import ALLOWED_STATUSES, assert_transition, next_actions


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

ALLOWED_REPORT_STATUSES = ALLOWED_STATUSES


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
    branding_raw = getattr(row, "branding_json", None) or "{}"
    try:
        branding = json.loads(branding_raw)
    except json.JSONDecodeError:
        branding = {}
    return {
        "id": row.id,
        "name": row.name,
        "short_name": row.short_name,
        "url": row.website_url,
        "verified": bool(row.verified),
        "handles": json.loads(row.handles_json or "[]"),
        "branding": branding if isinstance(branding, dict) else {},
        "contact_email": getattr(row, "contact_email", None),
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
        "mfa_enabled": bool(getattr(row, "mfa_enabled", False)),
        "oidc_provider": getattr(row, "oidc_provider", None),
        "auth_provider": getattr(row, "auth_provider", None) or "local",
        "must_reset_password": bool(getattr(row, "must_reset_password", False)),
        "last_login_at": getattr(row, "last_login_at", None),
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
            mfa_enabled=False,
            mfa_secret=None,
            auth_provider="local",
            must_reset_password=False,
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


def get_user_mfa_secret(user_id: int) -> str | None:
    with session_scope() as session:
        row = session.get(User, user_id)
        if not row:
            return None
        return row.mfa_secret


def begin_mfa_setup(user_id: int, secret: str) -> dict:
    with session_scope() as session:
        row = session.get(User, user_id)
        if not row:
            raise ValueError("User not found")
        row.mfa_secret = secret
        row.mfa_enabled = False
        session.flush()
        return _user_to_dict(row)


def enable_mfa(user_id: int) -> dict:
    with session_scope() as session:
        row = session.get(User, user_id)
        if not row or not row.mfa_secret:
            raise ValueError("MFA secret not initialized")
        row.mfa_enabled = True
        session.flush()
        return _user_to_dict(row)


def disable_mfa(user_id: int) -> dict:
    with session_scope() as session:
        row = session.get(User, user_id)
        if not row:
            raise ValueError("User not found")
        row.mfa_enabled = False
        row.mfa_secret = None
        session.flush()
        return _user_to_dict(row)


def create_partner_api_key(
    *,
    name: str,
    partner_org: str,
    scopes: list[str],
    created_by_user_id: int | None = None,
    expires_at: str | None = None,
) -> dict:
    name = (name or "").strip()
    partner_org = (partner_org or "").strip()
    if not name or not partner_org:
        raise ValueError("name and partner_org are required")
    if not scopes:
        raise ValueError("at least one scope is required")
    raw, prefix, digest = generate_api_key()
    with session_scope() as session:
        row = PartnerApiKey(
            name=name,
            partner_org=partner_org,
            key_prefix=prefix,
            key_hash=digest,
            scopes_json=json.dumps(scopes, ensure_ascii=True),
            created_by_user_id=created_by_user_id,
            revoked=False,
            expires_at=expires_at,
            last_used_at=None,
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        payload = _api_key_to_dict(row)
        payload["api_key"] = raw
        return payload


def _api_key_to_dict(row: PartnerApiKey) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "partner_org": row.partner_org,
        "key_prefix": row.key_prefix,
        "scopes": json.loads(row.scopes_json or "[]"),
        "created_by_user_id": row.created_by_user_id,
        "revoked": bool(row.revoked),
        "expires_at": row.expires_at,
        "last_used_at": row.last_used_at,
        "created_at": row.created_at,
    }


def list_partner_api_keys(include_revoked: bool = False) -> list[dict]:
    with session_scope() as session:
        rows = session.scalars(select(PartnerApiKey).order_by(PartnerApiKey.id.desc())).all()
        items = []
        for row in rows:
            if row.revoked and not include_revoked:
                continue
            items.append(_api_key_to_dict(row))
        return items


def revoke_partner_api_key(key_id: int) -> dict | None:
    with session_scope() as session:
        row = session.get(PartnerApiKey, key_id)
        if not row:
            return None
        row.revoked = True
        session.flush()
        return _api_key_to_dict(row)


def authenticate_api_key(raw_key: str) -> dict | None:
    if not raw_key:
        return None
    if raw_key.startswith("msi_"):
        from .institution_store import authenticate_institution_api_key

        return authenticate_institution_api_key(raw_key)
    if not raw_key.startswith("msb_"):
        return None
    digest = hash_api_key(raw_key)
    with session_scope() as session:
        row = session.scalar(select(PartnerApiKey).where(PartnerApiKey.key_hash == digest))
        if not row or row.revoked:
            return None
        if row.expires_at:
            try:
                expires = datetime.fromisoformat(row.expires_at)
                if expires.tzinfo is None:
                    expires = expires.replace(tzinfo=timezone.utc)
                if expires < datetime.now(timezone.utc):
                    return None
            except ValueError:
                return None
        row.last_used_at = now_iso()
        return {
            "id": row.id,
            "name": row.name,
            "partner_org": row.partner_org,
            "scopes": json.loads(row.scopes_json or "[]"),
            "role": "partner",
            "is_active": True,
            "auth_type": "api_key",
            "key_type": "partner",
        }


def _row_to_incident(row: IncidentReport) -> dict:
    ai_summary = None
    if row.ai_summary_json:
        try:
            ai_summary = json.loads(row.ai_summary_json)
        except json.JSONDecodeError:
            ai_summary = {"raw": row.ai_summary_json}
    return {
        "id": row.id,
        "verification_check_id": row.verification_check_id,
        "user_id": row.user_id,
        "report_type": row.report_type,
        "description": row.description,
        "status": row.status,
        "reviewer_note": row.reviewer_note,
        "priority": getattr(row, "priority", None) or "normal",
        "region": getattr(row, "region", None),
        "assigned_to_user_id": getattr(row, "assigned_to_user_id", None),
        "institution_id": getattr(row, "institution_id", None),
        "decision_summary": getattr(row, "decision_summary", None),
        "public_advisory": getattr(row, "public_advisory", None),
        "ai_summary": ai_summary,
        "next_actions": next_actions(row.status),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _append_incident_event(
    session,
    *,
    incident_id: int,
    from_status: str | None,
    to_status: str,
    actor_user_id: int | None = None,
    actor_role: str | None = None,
    note: str | None = None,
    details: dict | None = None,
) -> None:
    session.add(
        IncidentEvent(
            incident_id=incident_id,
            from_status=from_status,
            to_status=to_status,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            note=note,
            details_json=json.dumps(details or {}, ensure_ascii=True),
            created_at=now_iso(),
        )
    )


def _ai_summary_from_check(check: dict | None) -> dict | None:
    if not check:
        return None
    result = check.get("result") or {}
    analysis = result.get("ai_analysis") or {}
    return {
        "check_id": check.get("id"),
        "risk_score": check.get("risk_score") or result.get("risk_score"),
        "risk_band": check.get("risk_band") or result.get("risk_band"),
        "confidence": analysis.get("confidence"),
        "threat_categories": analysis.get("threat_categories") or [],
        "narrative": analysis.get("narrative"),
        "engine": analysis.get("engine"),
    }


def create_incident_report(
    *,
    report_type: str,
    description: str,
    verification_check_id: int | None = None,
    user_id: int | None = None,
    region: str | None = None,
    priority: str = "normal",
    institution_id: str | None = None,
    auto_ai: bool = True,
) -> dict:
    report_type = (report_type or "").strip().lower()
    description = (description or "").strip()
    if report_type not in ALLOWED_REPORT_TYPES:
        raise ValueError(f"Invalid report_type. Allowed: {', '.join(sorted(ALLOWED_REPORT_TYPES))}")
    if len(description) < 8:
        raise ValueError("description must be at least 8 characters")
    check = None
    if verification_check_id is not None:
        check = get_verification_check(verification_check_id)
        if not check:
            raise ValueError("verification_check_id not found")
    if user_id is not None and not get_user(user_id):
        raise ValueError("user_id not found")
    if institution_id is not None and not get_institution(institution_id):
        raise ValueError("institution_id not found")

    stamp = now_iso()
    ai_summary = _ai_summary_from_check(check) if auto_ai else None
    initial_status = "ai_analysis" if (auto_ai and ai_summary) else "open"

    with session_scope() as session:
        row = IncidentReport(
            verification_check_id=verification_check_id,
            user_id=user_id,
            report_type=report_type,
            description=description,
            status=initial_status,
            reviewer_note=None,
            priority=(priority or "normal").strip().lower() or "normal",
            region=(region or "").strip() or None,
            institution_id=institution_id,
            ai_summary_json=json.dumps(ai_summary, ensure_ascii=True) if ai_summary else None,
            created_at=stamp,
            updated_at=stamp,
        )
        session.add(row)
        session.flush()
        _append_incident_event(
            session,
            incident_id=row.id,
            from_status=None,
            to_status="open",
            actor_user_id=user_id,
            actor_role="citizen",
            note="Citizen report submitted",
        )
        if initial_status == "ai_analysis":
            _append_incident_event(
                session,
                incident_id=row.id,
                from_status="open",
                to_status="ai_analysis",
                actor_role="system",
                note="Automatic AI analysis attached from linked verification check",
                details=ai_summary or {},
            )
        session.flush()
        return _row_to_incident(row)


def get_incident_report(report_id: int) -> dict | None:
    with session_scope() as session:
        row = session.get(IncidentReport, report_id)
        if not row:
            return None
        return _row_to_incident(row)


def list_incident_reports(
    limit: int = 20,
    status: str | None = None,
    user_id: int | None = None,
    statuses: list[str] | None = None,
) -> list[dict]:
    safe_limit = max(1, min(limit, 100))
    with session_scope() as session:
        stmt = select(IncidentReport).order_by(IncidentReport.id.desc()).limit(safe_limit)
        filters = []
        if status:
            if status not in ALLOWED_REPORT_STATUSES:
                raise ValueError(f"Invalid status. Allowed: {', '.join(sorted(ALLOWED_REPORT_STATUSES))}")
            filters.append(IncidentReport.status == status)
        if statuses:
            for item in statuses:
                if item not in ALLOWED_REPORT_STATUSES:
                    raise ValueError(f"Invalid status. Allowed: {', '.join(sorted(ALLOWED_REPORT_STATUSES))}")
            filters.append(IncidentReport.status.in_(statuses))
        if user_id is not None:
            filters.append(IncidentReport.user_id == user_id)
        if filters:
            stmt = select(IncidentReport).where(*filters).order_by(IncidentReport.id.desc()).limit(safe_limit)
        rows = session.scalars(stmt).all()
        return [_row_to_incident(row) for row in rows]


def update_incident_status(
    report_id: int,
    *,
    status: str,
    reviewer_note: str | None = None,
    actor_user_id: int | None = None,
    actor_role: str | None = None,
    decision_summary: str | None = None,
    public_advisory: str | None = None,
    assigned_to_user_id: int | None = None,
    institution_id: str | None = None,
    region: str | None = None,
    priority: str | None = None,
) -> dict | None:
    with session_scope() as session:
        row = session.get(IncidentReport, report_id)
        if not row:
            return None
        _, persist_status = assert_transition(row.status, status)
        from_status = row.status
        row.status = persist_status
        if reviewer_note is not None:
            row.reviewer_note = reviewer_note
        if decision_summary is not None:
            row.decision_summary = decision_summary
        if public_advisory is not None:
            row.public_advisory = public_advisory
        if assigned_to_user_id is not None:
            row.assigned_to_user_id = assigned_to_user_id
        if institution_id is not None:
            row.institution_id = institution_id
        if region is not None:
            row.region = region
        if priority is not None:
            row.priority = priority
        row.updated_at = now_iso()
        _append_incident_event(
            session,
            incident_id=row.id,
            from_status=from_status,
            to_status=persist_status,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            note=reviewer_note,
            details={
                "decision_summary": decision_summary,
                "public_advisory": public_advisory,
                "institution_id": institution_id,
            },
        )
        session.flush()
        return _row_to_incident(row)


def list_incident_events(incident_id: int) -> list[dict]:
    with session_scope() as session:
        if not session.get(IncidentReport, incident_id):
            return []
        rows = session.scalars(
            select(IncidentEvent)
            .where(IncidentEvent.incident_id == incident_id)
            .order_by(IncidentEvent.id.asc())
        ).all()
        return [
            {
                "id": row.id,
                "incident_id": row.incident_id,
                "from_status": row.from_status,
                "to_status": row.to_status,
                "actor_user_id": row.actor_user_id,
                "actor_role": row.actor_role,
                "note": row.note,
                "details": json.loads(row.details_json or "{}"),
                "created_at": row.created_at,
            }
            for row in rows
        ]


def incident_status_counts() -> dict[str, int]:
    with session_scope() as session:
        rows = session.scalars(select(IncidentReport)).all()
        counts: dict[str, int] = {}
        for row in rows:
            counts[row.status] = counts.get(row.status, 0) + 1
        return counts


def list_verification_checks_for_user(user_id: int, limit: int = 20) -> list[dict]:
    safe_limit = max(1, min(limit, 100))
    with session_scope() as session:
        checks = session.scalars(
            select(VerificationCheck)
            .where(VerificationCheck.user_id == user_id)
            .order_by(VerificationCheck.id.desc())
            .limit(safe_limit)
        ).all()
        items = []
        for check in checks:
            items.append(_row_to_check(check, []))
        return items


def upsert_institution(
    *,
    institution_id: str,
    name: str,
    short_name: str,
    url: str | None = None,
    verified: bool = True,
    handles: list[str] | None = None,
) -> dict:
    institution_id = (institution_id or "").strip().lower()
    name = (name or "").strip()
    short_name = (short_name or "").strip()
    if not institution_id or not name or not short_name:
        raise ValueError("id, name, and short_name are required")
    handles = handles or []
    with session_scope() as session:
        row = session.get(Institution, institution_id)
        if row:
            row.name = name
            row.short_name = short_name
            row.website_url = url or ""
            row.verified = 1 if verified else 0
            row.handles_json = json.dumps(handles, ensure_ascii=True)
        else:
            row = Institution(
                id=institution_id,
                name=name,
                short_name=short_name,
                website_url=url or "",
                verified=1 if verified else 0,
                handles_json=json.dumps(handles, ensure_ascii=True),
                branding_json="{}",
                created_at=now_iso(),
            )
            session.add(row)
        session.flush()
        return _row_to_institution(row)


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
