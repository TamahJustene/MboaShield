"""Evidence package signing and custody chain hashing."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from ...core.config import get_settings


def vault_signing_key() -> bytes:
    settings = get_settings()
    raw = (settings.vault_signing_key or "").strip() or settings.jwt_secret
    return raw.encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sign_payload(payload: dict[str, Any] | str | bytes) -> str:
    if isinstance(payload, dict):
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    elif isinstance(payload, str):
        body = payload.encode("utf-8")
    else:
        body = payload
    return hmac.new(vault_signing_key(), body, hashlib.sha256).hexdigest()


def verify_signature(payload: dict[str, Any] | str | bytes, signature: str) -> bool:
    expected = sign_payload(payload)
    return hmac.compare_digest(expected, signature)


def custody_event_hash(
    *,
    evidence_id: str,
    event_type: str,
    created_at: str,
    from_user_id: int | None,
    to_user_id: int | None,
    note: str | None,
    prev_event_hash: str | None,
) -> str:
    material = "|".join(
        [
            evidence_id,
            event_type,
            created_at,
            str(from_user_id or ""),
            str(to_user_id or ""),
            note or "",
            prev_event_hash or "",
        ]
    )
    return sha256_hex(material.encode("utf-8"))
