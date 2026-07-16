"""In-app notifications with optional webhook delivery hook."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..core.config import get_settings
from ..ntoc_store import create_notification, mark_notification_webhook_delivered

logger = logging.getLogger("mboashield.notifications")


def notify(
    *,
    title: str,
    body: str,
    audience: str = "analyst",
    user_id: int | None = None,
    category: str = "ops",
    resource_type: str | None = None,
    resource_id: str | None = None,
) -> dict[str, Any]:
    item = create_notification(
        title=title,
        body=body,
        audience=audience,
        user_id=user_id,
        category=category,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    _deliver_webhook(item)
    return item


def notify_incident_transition(
    *,
    incident_id: int,
    to_status: str,
    actor_user_id: int | None = None,
) -> dict[str, Any]:
    return notify(
        title=f"Incident #{incident_id} ? {to_status}",
        body=f"National workflow advanced to '{to_status}'.",
        audience="analyst",
        user_id=actor_user_id,
        category="incident",
        resource_type="incident",
        resource_id=str(incident_id),
    )


def notify_case_assignment(
    *,
    case_id: int,
    assignee_user_id: int,
    title: str,
) -> dict[str, Any]:
    return notify(
        title=f"Case assigned: {title}",
        body=f"Investigation case #{case_id} was assigned to you.",
        audience="analyst",
        user_id=assignee_user_id,
        category="case",
        resource_type="case",
        resource_id=str(case_id),
    )


def _deliver_webhook(item: dict[str, Any]) -> None:
    settings = get_settings()
    url = (settings.notification_webhook_url or "").strip()
    if not url:
        return
    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.post(url, json={"event": "notification", "notification": item})
            if response.status_code < 400:
                mark_notification_webhook_delivered(item["id"])
            else:
                logger.warning("notification webhook HTTP %s", response.status_code)
    except Exception as exc:  # noqa: BLE001 - delivery must not break ops path
        logger.warning("notification webhook failed: %s", exc)
