"""Interoperability persistence - outbound webhooks (T4)."""

from __future__ import annotations

import json
import secrets
from typing import Any

from sqlalchemy import select

from .db.models import WebhookDelivery, WebhookEndpoint
from .db.session import session_scope
from .repositories import now_iso

EVENT_CATALOG = [
    {
        "id": "trust.assessment.created",
        "description": "A TrustAssessment was persisted",
    },
    {
        "id": "trust_network.alert.shared",
        "description": "A shared alert was published on the Trust Network",
    },
    {
        "id": "incident.status_changed",
        "description": "Incident workflow status changed",
    },
    {
        "id": "announcement.published",
        "description": "A verified government announcement was published",
    },
    {
        "id": "interop.ping",
        "description": "Test ping for subscription verification",
    },
]


def _endpoint_dict(row: WebhookEndpoint) -> dict[str, Any]:
    return {
        "id": row.id,
        "name": row.name,
        "url": row.url,
        "events": json.loads(row.events_json or "[]"),
        "enabled": row.enabled,
        "partner_org": row.partner_org,
        "has_secret": bool(row.secret),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _delivery_dict(row: WebhookDelivery) -> dict[str, Any]:
    return {
        "id": row.id,
        "endpoint_id": row.endpoint_id,
        "event_type": row.event_type,
        "status": row.status,
        "attempts": row.attempts,
        "last_status_code": row.last_status_code,
        "last_error": row.last_error,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def create_webhook_endpoint(
    *,
    name: str,
    url: str,
    events: list[str] | None = None,
    partner_org: str = "",
    secret: str | None = None,
    enabled: bool = True,
    created_by_user_id: int | None = None,
) -> dict[str, Any]:
    if not url.startswith("http://") and not url.startswith("https://"):
        raise ValueError("url must start with http:// or https://")
    known = {item["id"] for item in EVENT_CATALOG}
    selected = events or ["interop.ping"]
    for event in selected:
        if event not in known and event != "*":
            raise ValueError(f"Unknown event type: {event}")
    stamp = now_iso()
    raw_secret = secret or secrets.token_urlsafe(24)
    with session_scope() as session:
        row = WebhookEndpoint(
            name=name,
            url=url,
            secret=raw_secret,
            events_json=json.dumps(selected, ensure_ascii=True),
            enabled=enabled,
            partner_org=partner_org or "",
            created_by_user_id=created_by_user_id,
            created_at=stamp,
            updated_at=stamp,
        )
        session.add(row)
        session.flush()
        payload = _endpoint_dict(row)
        payload["secret"] = raw_secret  # shown once
        return payload


def list_webhook_endpoints(*, enabled_only: bool = False) -> list[dict[str, Any]]:
    with session_scope() as session:
        stmt = select(WebhookEndpoint).order_by(WebhookEndpoint.id.desc())
        if enabled_only:
            stmt = stmt.where(WebhookEndpoint.enabled.is_(True))
        return [_endpoint_dict(row) for row in session.scalars(stmt).all()]


def get_webhook_endpoint(endpoint_id: int) -> dict[str, Any] | None:
    with session_scope() as session:
        row = session.get(WebhookEndpoint, endpoint_id)
        if not row:
            return None
        data = _endpoint_dict(row)
        data["_secret"] = row.secret
        data["_url"] = row.url
        data["_events"] = json.loads(row.events_json or "[]")
        return data


def set_webhook_endpoint_enabled(endpoint_id: int, *, enabled: bool) -> dict[str, Any] | None:
    stamp = now_iso()
    with session_scope() as session:
        row = session.get(WebhookEndpoint, endpoint_id)
        if not row:
            return None
        row.enabled = enabled
        row.updated_at = stamp
        session.flush()
        return _endpoint_dict(row)


def create_delivery(
    *,
    endpoint_id: int,
    event_type: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    stamp = now_iso()
    with session_scope() as session:
        row = WebhookDelivery(
            endpoint_id=endpoint_id,
            event_type=event_type,
            payload_json=json.dumps(payload, ensure_ascii=True),
            status="pending",
            attempts=0,
            created_at=stamp,
            updated_at=stamp,
        )
        session.add(row)
        session.flush()
        return _delivery_dict(row)


def update_delivery(
    delivery_id: int,
    *,
    status: str,
    attempts: int,
    last_status_code: int | None = None,
    last_error: str | None = None,
) -> dict[str, Any] | None:
    stamp = now_iso()
    with session_scope() as session:
        row = session.get(WebhookDelivery, delivery_id)
        if not row:
            return None
        row.status = status
        row.attempts = attempts
        row.last_status_code = last_status_code
        row.last_error = last_error
        row.updated_at = stamp
        session.flush()
        return _delivery_dict(row)


def list_deliveries(*, endpoint_id: int | None = None, limit: int = 50) -> list[dict[str, Any]]:
    safe = max(1, min(limit, 200))
    with session_scope() as session:
        stmt = select(WebhookDelivery).order_by(WebhookDelivery.id.desc()).limit(safe)
        if endpoint_id is not None:
            stmt = (
                select(WebhookDelivery)
                .where(WebhookDelivery.endpoint_id == endpoint_id)
                .order_by(WebhookDelivery.id.desc())
                .limit(safe)
            )
        return [_delivery_dict(row) for row in session.scalars(stmt).all()]


def get_delivery_payload(delivery_id: int) -> dict[str, Any] | None:
    with session_scope() as session:
        row = session.get(WebhookDelivery, delivery_id)
        if not row:
            return None
        return {
            **_delivery_dict(row),
            "payload": json.loads(row.payload_json or "{}"),
        }
