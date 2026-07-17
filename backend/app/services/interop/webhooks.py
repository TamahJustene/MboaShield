"""Outbound webhook delivery with HMAC signatures and retries (T4)."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from typing import Any

import httpx

from ...core.config import get_settings
from ...interop_store import (
    EVENT_CATALOG,
    create_delivery,
    get_webhook_endpoint,
    list_webhook_endpoints,
    update_delivery,
)
from ...repositories import now_iso

logger = logging.getLogger("mboashield.interop.webhooks")


def signing_secret(endpoint_secret: str | None = None) -> str:
    settings = get_settings()
    if endpoint_secret:
        return endpoint_secret
    return (settings.webhook_signing_secret or settings.jwt_secret or "mboashield-demo").strip()


def sign_payload(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_signature(body: bytes, signature_header: str, secret: str) -> bool:
    expected = sign_payload(body, secret)
    return hmac.compare_digest(expected, (signature_header or "").strip())


def event_catalog() -> list[dict[str, str]]:
    return list(EVENT_CATALOG)


def _matches(events: list[str], event_type: str) -> bool:
    return "*" in events or event_type in events


def emit_event(event_type: str, data: dict[str, Any], *, sync_deliver: bool = True) -> dict[str, Any]:
    """Fan-out an event to matching enabled endpoints."""
    envelope = {
        "id": f"evt_{int(time.time() * 1000)}",
        "type": event_type,
        "created_at": now_iso(),
        "data": data,
    }
    deliveries: list[dict[str, Any]] = []
    for endpoint in list_webhook_endpoints(enabled_only=True):
        full = get_webhook_endpoint(endpoint["id"])
        if not full:
            continue
        if not _matches(full.get("_events") or [], event_type):
            continue
        delivery = create_delivery(
            endpoint_id=endpoint["id"],
            event_type=event_type,
            payload=envelope,
        )
        if sync_deliver:
            delivery = deliver_now(delivery["id"], endpoint_id=endpoint["id"], envelope=envelope)
        deliveries.append(delivery)
    return {"event": envelope, "deliveries": deliveries, "count": len(deliveries)}


def deliver_now(
    delivery_id: int,
    *,
    endpoint_id: int,
    envelope: dict[str, Any] | None = None,
    max_attempts: int | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    attempts_budget = max_attempts or settings.webhook_max_retries
    endpoint = get_webhook_endpoint(endpoint_id)
    if not endpoint:
        return update_delivery(delivery_id, status="failed", attempts=0, last_error="endpoint missing") or {}

    body_obj = envelope
    if body_obj is None:
        from ...interop_store import get_delivery_payload

        packed = get_delivery_payload(delivery_id)
        body_obj = (packed or {}).get("payload") or {}

    body = json.dumps(body_obj, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    secret = signing_secret(endpoint.get("_secret"))
    signature = sign_payload(body, secret)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "MboaShield-Interop/2.4",
        "X-MboaShield-Signature": signature,
        "X-MboaShield-Event": str(body_obj.get("type") or ""),
        "X-MboaShield-Delivery": str(delivery_id),
    }

    last_code: int | None = None
    last_error: str | None = None
    attempts = 0
    for attempt in range(1, attempts_budget + 1):
        attempts = attempt
        try:
            with httpx.Client(timeout=8.0) as client:
                response = client.post(endpoint["_url"], content=body, headers=headers)
            last_code = response.status_code
            if 200 <= response.status_code < 300:
                return (
                    update_delivery(
                        delivery_id,
                        status="delivered",
                        attempts=attempts,
                        last_status_code=last_code,
                        last_error=None,
                    )
                    or {}
                )
            last_error = f"HTTP {response.status_code}"
        except Exception as exc:  # noqa: BLE001 - record delivery failure
            last_error = str(exc)
            logger.warning("webhook delivery failed endpoint=%s: %s", endpoint_id, exc)
        if attempt < attempts_budget:
            time.sleep(min(0.05 * attempt, 0.2))

    return (
        update_delivery(
            delivery_id,
            status="failed",
            attempts=attempts,
            last_status_code=last_code,
            last_error=last_error,
        )
        or {}
    )
