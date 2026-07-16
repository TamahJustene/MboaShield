"""Phase 7 NTOC persistence: cases, notes, assignments, notifications, health."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import or_, select

from .db.models import (
    CaseAssignment,
    CaseNote,
    Institution,
    InstitutionHealthSnapshot,
    InvestigationCase,
    Notification,
)
from .db.session import session_scope
from .repositories import get_incident_report, get_user, get_verification_check, now_iso

CASE_STATUSES = {"intake", "investigating", "pending_institution", "closed"}
CASE_PRIORITIES = {"low", "normal", "high", "critical"}


def _case_to_dict(row: InvestigationCase) -> dict:
    return {
        "id": row.id,
        "title": row.title,
        "summary": row.summary,
        "status": row.status,
        "priority": row.priority,
        "region": row.region,
        "incident_id": row.incident_id,
        "verification_check_id": row.verification_check_id,
        "institution_id": row.institution_id,
        "created_by_user_id": row.created_by_user_id,
        "assigned_to_user_id": row.assigned_to_user_id,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def create_case(
    *,
    title: str,
    summary: str | None = None,
    incident_id: int | None = None,
    verification_check_id: int | None = None,
    institution_id: str | None = None,
    region: str | None = None,
    priority: str = "normal",
    created_by_user_id: int | None = None,
    assigned_to_user_id: int | None = None,
) -> dict:
    title = (title or "").strip()
    if len(title) < 3:
        raise ValueError("title must be at least 3 characters")
    priority = (priority or "normal").strip().lower()
    if priority not in CASE_PRIORITIES:
        raise ValueError(f"Invalid priority. Allowed: {', '.join(sorted(CASE_PRIORITIES))}")
    if incident_id is not None and not get_incident_report(incident_id):
        raise ValueError("incident_id not found")
    if verification_check_id is not None and not get_verification_check(verification_check_id):
        raise ValueError("verification_check_id not found")
    if assigned_to_user_id is not None and not get_user(assigned_to_user_id):
        raise ValueError("assigned_to_user_id not found")
    stamp = now_iso()
    with session_scope() as session:
        if institution_id and not session.get(Institution, institution_id):
            raise ValueError("institution_id not found")
        row = InvestigationCase(
            title=title,
            summary=(summary or "").strip() or None,
            status="intake",
            priority=priority,
            region=(region or "").strip() or None,
            incident_id=incident_id,
            verification_check_id=verification_check_id,
            institution_id=institution_id,
            created_by_user_id=created_by_user_id,
            assigned_to_user_id=assigned_to_user_id,
            created_at=stamp,
            updated_at=stamp,
        )
        session.add(row)
        session.flush()
        if assigned_to_user_id is not None:
            session.add(
                CaseAssignment(
                    case_id=row.id,
                    assignee_user_id=assigned_to_user_id,
                    assigned_by_user_id=created_by_user_id,
                    note="Initial assignment",
                    created_at=stamp,
                )
            )
        return _case_to_dict(row)


def get_case(case_id: int) -> dict | None:
    with session_scope() as session:
        row = session.get(InvestigationCase, case_id)
        return _case_to_dict(row) if row else None


def update_case(
    case_id: int,
    *,
    status: str | None = None,
    priority: str | None = None,
    summary: str | None = None,
    title: str | None = None,
    region: str | None = None,
    assigned_to_user_id: int | None = None,
    assigned_by_user_id: int | None = None,
    assignment_note: str | None = None,
) -> dict:
    with session_scope() as session:
        row = session.get(InvestigationCase, case_id)
        if not row:
            raise ValueError("Case not found")
        if status is not None:
            status = status.strip().lower()
            if status not in CASE_STATUSES:
                raise ValueError(f"Invalid status. Allowed: {', '.join(sorted(CASE_STATUSES))}")
            row.status = status
        if priority is not None:
            priority = priority.strip().lower()
            if priority not in CASE_PRIORITIES:
                raise ValueError(f"Invalid priority. Allowed: {', '.join(sorted(CASE_PRIORITIES))}")
            row.priority = priority
        if summary is not None:
            row.summary = summary.strip() or None
        if title is not None and title.strip():
            row.title = title.strip()
        if region is not None:
            row.region = region.strip() or None
        if assigned_to_user_id is not None:
            if not get_user(assigned_to_user_id):
                raise ValueError("assigned_to_user_id not found")
            row.assigned_to_user_id = assigned_to_user_id
            session.add(
                CaseAssignment(
                    case_id=row.id,
                    assignee_user_id=assigned_to_user_id,
                    assigned_by_user_id=assigned_by_user_id,
                    note=(assignment_note or "").strip() or None,
                    created_at=now_iso(),
                )
            )
        row.updated_at = now_iso()
        session.flush()
        return _case_to_dict(row)


def search_cases(
    *,
    q: str | None = None,
    status: str | None = None,
    assigned_to_user_id: int | None = None,
    incident_id: int | None = None,
    limit: int = 50,
) -> list[dict]:
    safe_limit = max(1, min(limit, 200))
    with session_scope() as session:
        stmt = select(InvestigationCase).order_by(InvestigationCase.id.desc()).limit(safe_limit)
        filters = []
        if status:
            filters.append(InvestigationCase.status == status)
        if assigned_to_user_id is not None:
            filters.append(InvestigationCase.assigned_to_user_id == assigned_to_user_id)
        if incident_id is not None:
            filters.append(InvestigationCase.incident_id == incident_id)
        if q and q.strip():
            needle = f"%{q.strip().lower()}%"
            filters.append(
                or_(
                    InvestigationCase.title.ilike(needle),
                    InvestigationCase.summary.ilike(needle),
                    InvestigationCase.region.ilike(needle),
                )
            )
        if filters:
            stmt = select(InvestigationCase).where(*filters).order_by(InvestigationCase.id.desc()).limit(safe_limit)
        return [_case_to_dict(row) for row in session.scalars(stmt).all()]


def add_case_note(
    case_id: int,
    *,
    body: str,
    author_user_id: int | None = None,
    author_role: str | None = None,
) -> dict:
    text = (body or "").strip()
    if len(text) < 2:
        raise ValueError("note body must be at least 2 characters")
    with session_scope() as session:
        if not session.get(InvestigationCase, case_id):
            raise ValueError("Case not found")
        row = CaseNote(
            case_id=case_id,
            author_user_id=author_user_id,
            author_role=author_role,
            body=text,
            created_at=now_iso(),
        )
        session.add(row)
        case = session.get(InvestigationCase, case_id)
        if case:
            case.updated_at = now_iso()
        session.flush()
        return {
            "id": row.id,
            "case_id": row.case_id,
            "author_user_id": row.author_user_id,
            "author_role": row.author_role,
            "body": row.body,
            "created_at": row.created_at,
        }


def list_case_notes(case_id: int) -> list[dict]:
    with session_scope() as session:
        rows = session.scalars(
            select(CaseNote).where(CaseNote.case_id == case_id).order_by(CaseNote.id.asc())
        ).all()
        return [
            {
                "id": row.id,
                "case_id": row.case_id,
                "author_user_id": row.author_user_id,
                "author_role": row.author_role,
                "body": row.body,
                "created_at": row.created_at,
            }
            for row in rows
        ]


def list_case_assignments(case_id: int) -> list[dict]:
    with session_scope() as session:
        rows = session.scalars(
            select(CaseAssignment).where(CaseAssignment.case_id == case_id).order_by(CaseAssignment.id.asc())
        ).all()
        return [
            {
                "id": row.id,
                "case_id": row.case_id,
                "assignee_user_id": row.assignee_user_id,
                "assigned_by_user_id": row.assigned_by_user_id,
                "note": row.note,
                "created_at": row.created_at,
            }
            for row in rows
        ]


def create_notification(
    *,
    title: str,
    body: str,
    audience: str = "analyst",
    user_id: int | None = None,
    category: str = "ops",
    resource_type: str | None = None,
    resource_id: str | None = None,
) -> dict:
    with session_scope() as session:
        row = Notification(
            user_id=user_id,
            audience=audience,
            title=title.strip()[:255],
            body=body.strip(),
            category=category,
            resource_type=resource_type,
            resource_id=resource_id,
            read=False,
            webhook_delivered=False,
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        return _notification_to_dict(row)


def list_notifications(
    *,
    audience: str | None = None,
    user_id: int | None = None,
    unread_only: bool = False,
    limit: int = 50,
) -> list[dict]:
    safe_limit = max(1, min(limit, 200))
    with session_scope() as session:
        stmt = select(Notification).order_by(Notification.id.desc()).limit(safe_limit)
        filters = []
        if audience:
            filters.append(Notification.audience == audience)
        if user_id is not None:
            filters.append(or_(Notification.user_id == user_id, Notification.user_id.is_(None)))
        if unread_only:
            filters.append(Notification.read.is_(False))
        if filters:
            stmt = select(Notification).where(*filters).order_by(Notification.id.desc()).limit(safe_limit)
        return [_notification_to_dict(row) for row in session.scalars(stmt).all()]


def mark_notification_read(notification_id: int) -> dict | None:
    with session_scope() as session:
        row = session.get(Notification, notification_id)
        if not row:
            return None
        row.read = True
        session.flush()
        return _notification_to_dict(row)


def mark_notification_webhook_delivered(notification_id: int) -> None:
    with session_scope() as session:
        row = session.get(Notification, notification_id)
        if row:
            row.webhook_delivered = True


def _notification_to_dict(row: Notification) -> dict:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "audience": row.audience,
        "title": row.title,
        "body": row.body,
        "category": row.category,
        "resource_type": row.resource_type,
        "resource_id": row.resource_id,
        "read": bool(row.read),
        "webhook_delivered": bool(row.webhook_delivered),
        "created_at": row.created_at,
    }


def save_institution_health_snapshots(items: list[dict[str, Any]]) -> list[dict]:
    stamp = now_iso()
    saved: list[dict] = []
    with session_scope() as session:
        for item in items:
            row = InstitutionHealthSnapshot(
                institution_id=item["institution_id"],
                health_score=int(item["health_score"]),
                open_incidents=int(item.get("open_incidents") or 0),
                high_risk_checks=int(item.get("high_risk_checks") or 0),
                details_json=json.dumps(item.get("details") or {}, ensure_ascii=True),
                created_at=stamp,
            )
            session.add(row)
            session.flush()
            saved.append(
                {
                    "id": row.id,
                    "institution_id": row.institution_id,
                    "health_score": row.health_score,
                    "open_incidents": row.open_incidents,
                    "high_risk_checks": row.high_risk_checks,
                    "details": item.get("details") or {},
                    "created_at": row.created_at,
                }
            )
    return saved


def evidence_for_case(case_id: int) -> dict[str, Any]:
    """Evidence viewer: linked incident/check plus vault items for the case."""
    case = get_case(case_id)
    if not case:
        raise ValueError("Case not found")
    incident = get_incident_report(case["incident_id"]) if case.get("incident_id") else None
    check_id = case.get("verification_check_id") or (incident or {}).get("verification_check_id")
    check = get_verification_check(check_id) if check_id else None
    linked = (
        [
            {
                "type": "verification_check",
                "id": check["id"],
                "check_type": check.get("check_type"),
                "risk_score": check.get("risk_score"),
                "risk_band": check.get("risk_band"),
                "created_at": check.get("created_at"),
            }
        ]
        if check
        else []
    )
    vault_items: list[dict[str, Any]] = []
    try:
        from .vault_store import list_evidence

        vault_items = list_evidence(case_id=case_id, limit=50)
    except Exception:
        vault_items = []
    return {
        "case_id": case_id,
        "incident": incident,
        "verification_check": check,
        "evidence_items": linked,
        "vault_items": vault_items,
        "note": "Linked verification checks plus Digital Evidence Vault items for this case.",
    }
