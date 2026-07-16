"""Digital signing for verified government announcements."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from ...core.config import get_settings


def announcement_signing_key() -> bytes:
    settings = get_settings()
    raw = (settings.announcement_signing_key or "").strip()
    if not raw:
        raw = (settings.vault_signing_key or "").strip() or settings.jwt_secret
    return raw.encode("utf-8")


def signing_kid() -> str:
    settings = get_settings()
    kid = (settings.announcement_signing_kid or "").strip()
    return kid or "mboashield-announce-v1"


def canonical_announcement_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_announcement_payload(payload: dict[str, Any]) -> tuple[str, str]:
    body = canonical_announcement_bytes(payload)
    content_hash = hashlib.sha256(body).hexdigest()
    signature = hmac.new(announcement_signing_key(), body, hashlib.sha256).hexdigest()
    return content_hash, signature


def verify_announcement_payload(payload: dict[str, Any], *, content_hash: str, signature: str) -> bool:
    body = canonical_announcement_bytes(payload)
    expected_hash = hashlib.sha256(body).hexdigest()
    if not hmac.compare_digest(expected_hash, content_hash):
        return False
    expected_sig = hmac.new(announcement_signing_key(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_sig, signature)
