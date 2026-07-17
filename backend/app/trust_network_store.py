"""National Digital Trust Network persistence (T2)."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import or_, select

from .db.models import ExchangeChannel, SharedAlert, TrustRelationship
from .db.session import session_scope
from .repositories import get_institution, now_iso

RELATIONSHIP_STATUSES = {"pending", "active", "suspended", "revoked"}
CHANNEL_TYPES = {"alert_share", "ioc_exchange", "advisory"}
ALERT_TYPES = {"impersonation", "deepfake", "fraud", "ioc", "advisory"}
SEVERITIES = {"low", "medium", "high", "critical"}


def _relationship_dict(row: TrustRelationship) -> dict[str, Any]:
    return {
        "id": row.id,
        "source_institution_id": row.source_institution_id,
        "target_institution_id": row.target_institution_id,
        "status": row.status,
        "policy_note": row.policy_note,
        "created_by_user_id": row.created_by_user_id,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _channel_dict(row: ExchangeChannel) -> dict[str, Any]:
    return {
        "id": row.id,
        "relationship_id": row.relationship_id,
        "channel_type": row.channel_type,
        "enabled": row.enabled,
        "label": row.label,
        "created_at": row.created_at,
    }


def _alert_dict(row: SharedAlert) -> dict[str, Any]:
    return {
        "id": row.id,
        "alert_type": row.alert_type,
        "title": row.title,
        "summary": row.summary,
        "severity": row.severity,
        "source_institution_id": row.source_institution_id,
        "target_institutions": json.loads(row.target_institutions_json or "[]"),
        "relationship_id": row.relationship_id,
        "verification_check_id": row.verification_check_id,
        "trust_assessment_id": row.trust_assessment_id,
        "payload": json.loads(row.payload_json or "{}"),
        "status": row.status,
        "created_by_user_id": row.created_by_user_id,
        "created_at": row.created_at,
    }


def create_relationship(
    *,
    source_institution_id: str,
    target_institution_id: str,
    status: str = "pending",
    policy_note: str = "",
    created_by_user_id: int | None = None,
) -> dict[str, Any]:
    if source_institution_id == target_institution_id:
        raise ValueError("Cannot create a trust relationship with the same institution")
    if not get_institution(source_institution_id):
        raise ValueError("source_institution_id not found")
    if not get_institution(target_institution_id):
        raise ValueError("target_institution_id not found")
    if status not in RELATIONSHIP_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    stamp = now_iso()
    with session_scope() as session:
        existing = session.scalars(
            select(TrustRelationship).where(
                TrustRelationship.source_institution_id == source_institution_id,
                TrustRelationship.target_institution_id == target_institution_id,
            )
        ).first()
        if existing:
            raise ValueError("Trust relationship already exists for this pair")
        row = TrustRelationship(
            source_institution_id=source_institution_id,
            target_institution_id=target_institution_id,
            status=status,
            policy_note=policy_note or "",
            created_by_user_id=created_by_user_id,
            created_at=stamp,
            updated_at=stamp,
        )
        session.add(row)
        session.flush()
        return _relationship_dict(row)


def list_relationships(
    *,
    institution_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    safe_limit = max(1, min(limit, 200))
    with session_scope() as session:
        stmt = select(TrustRelationship)
        if institution_id:
            stmt = stmt.where(
                or_(
                    TrustRelationship.source_institution_id == institution_id,
                    TrustRelationship.target_institution_id == institution_id,
                )
            )
        if status:
            stmt = stmt.where(TrustRelationship.status == status)
        stmt = stmt.order_by(TrustRelationship.id.desc()).limit(safe_limit)
        return [_relationship_dict(row) for row in session.scalars(stmt).all()]


def get_relationship(relationship_id: int) -> dict[str, Any] | None:
    with session_scope() as session:
        row = session.get(TrustRelationship, relationship_id)
        return _relationship_dict(row) if row else None


def update_relationship_status(
    relationship_id: int,
    *,
    status: str,
    policy_note: str | None = None,
) -> dict[str, Any] | None:
    if status not in RELATIONSHIP_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    stamp = now_iso()
    with session_scope() as session:
        row = session.get(TrustRelationship, relationship_id)
        if not row:
            return None
        row.status = status
        if policy_note is not None:
            row.policy_note = policy_note
        row.updated_at = stamp
        session.flush()
        return _relationship_dict(row)


def create_channel(
    *,
    relationship_id: int,
    channel_type: str,
    label: str = "",
    enabled: bool = True,
) -> dict[str, Any]:
    if channel_type not in CHANNEL_TYPES:
        raise ValueError(f"Invalid channel_type: {channel_type}")
    with session_scope() as session:
        rel = session.get(TrustRelationship, relationship_id)
        if not rel:
            raise ValueError("relationship not found")
        row = ExchangeChannel(
            relationship_id=relationship_id,
            channel_type=channel_type,
            enabled=enabled,
            label=label or channel_type,
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        return _channel_dict(row)


def list_channels(*, relationship_id: int | None = None, limit: int = 50) -> list[dict[str, Any]]:
    safe_limit = max(1, min(limit, 200))
    with session_scope() as session:
        stmt = select(ExchangeChannel).order_by(ExchangeChannel.id.desc()).limit(safe_limit)
        if relationship_id is not None:
            stmt = (
                select(ExchangeChannel)
                .where(ExchangeChannel.relationship_id == relationship_id)
                .order_by(ExchangeChannel.id.desc())
                .limit(safe_limit)
            )
        return [_channel_dict(row) for row in session.scalars(stmt).all()]


def create_shared_alert(
    *,
    alert_type: str,
    title: str,
    summary: str = "",
    severity: str = "medium",
    source_institution_id: str,
    target_institutions: list[str] | None = None,
    relationship_id: int | None = None,
    verification_check_id: int | None = None,
    trust_assessment_id: int | None = None,
    payload: dict | None = None,
    created_by_user_id: int | None = None,
) -> dict[str, Any]:
    if alert_type not in ALERT_TYPES:
        raise ValueError(f"Invalid alert_type: {alert_type}")
    if severity not in SEVERITIES:
        raise ValueError(f"Invalid severity: {severity}")
    if not get_institution(source_institution_id):
        raise ValueError("source_institution_id not found")
    targets = target_institutions or []
    for tid in targets:
        if not get_institution(tid):
            raise ValueError(f"target institution not found: {tid}")
    if relationship_id is not None:
        rel = get_relationship(relationship_id)
        if not rel:
            raise ValueError("relationship not found")
        if rel["status"] not in {"active", "pending"}:
            raise ValueError("relationship is not active for exchange")
    with session_scope() as session:
        row = SharedAlert(
            alert_type=alert_type,
            title=title,
            summary=summary or "",
            severity=severity,
            source_institution_id=source_institution_id,
            target_institutions_json=json.dumps(targets, ensure_ascii=True),
            relationship_id=relationship_id,
            verification_check_id=verification_check_id,
            trust_assessment_id=trust_assessment_id,
            payload_json=json.dumps(payload or {}, ensure_ascii=True),
            status="shared",
            created_by_user_id=created_by_user_id,
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        return _alert_dict(row)


def list_shared_alerts(
    *,
    institution_id: str | None = None,
    alert_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    safe_limit = max(1, min(limit, 200))
    with session_scope() as session:
        rows = session.scalars(
            select(SharedAlert).order_by(SharedAlert.id.desc()).limit(safe_limit * 3)
        ).all()
        items = [_alert_dict(row) for row in rows]
        if institution_id:
            items = [
                item
                for item in items
                if item["source_institution_id"] == institution_id
                or institution_id in (item.get("target_institutions") or [])
            ]
        if alert_type:
            items = [item for item in items if item["alert_type"] == alert_type]
        return items[:safe_limit]


def get_shared_alert(alert_id: int) -> dict[str, Any] | None:
    with session_scope() as session:
        row = session.get(SharedAlert, alert_id)
        return _alert_dict(row) if row else None


def network_status() -> dict[str, Any]:
    with session_scope() as session:
        relationships = session.scalars(select(TrustRelationship)).all()
        channels = session.scalars(select(ExchangeChannel)).all()
        alerts = session.scalars(select(SharedAlert)).all()
        by_status: dict[str, int] = {}
        for row in relationships:
            by_status[row.status] = by_status.get(row.status, 0) + 1
        by_type: dict[str, int] = {}
        for row in alerts:
            by_type[row.alert_type] = by_type.get(row.alert_type, 0) + 1
        return {
            "relationships_total": len(relationships),
            "relationships_by_status": by_status,
            "channels_total": len(channels),
            "alerts_total": len(alerts),
            "alerts_by_type": by_type,
            "alert_types": sorted(ALERT_TYPES),
            "channel_types": sorted(CHANNEL_TYPES),
        }
