"""Phase 6 identity persistence helpers (sessions, devices, resets, oauth clients, users admin)."""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select

from .core.config import get_settings
from .core.security import hash_password
from .db.models import (
    AuthEvent,
    AuthSession,
    OAuthClient,
    PasswordResetToken,
    Tenant,
    TrustedDevice,
    User,
)
from .db.session import session_scope
from .repositories import _user_to_dict, now_iso


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def ensure_default_tenant() -> dict:
    settings = get_settings()
    with session_scope() as session:
        row = session.get(Tenant, settings.tenant_id)
        if row:
            return {
                "id": row.id,
                "display_name": row.display_name,
                "deployment_profile": row.deployment_profile,
            }
        row = Tenant(
            id=settings.tenant_id,
            display_name=settings.tenant_display_name,
            deployment_profile=settings.deployment_profile,
            languages_json='["en","fr"]',
            config_json="{}",
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        return {
            "id": row.id,
            "display_name": row.display_name,
            "deployment_profile": row.deployment_profile,
        }


def write_auth_event(
    *,
    event_type: str,
    outcome: str = "success",
    user_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    with session_scope() as session:
        session.add(
            AuthEvent(
                user_id=user_id,
                event_type=event_type,
                outcome=outcome,
                ip_address=ip_address,
                user_agent=user_agent,
                details_json=json.dumps(details or {}, ensure_ascii=True),
                created_at=now_iso(),
            )
        )


def touch_user_login(user_id: int) -> None:
    with session_scope() as session:
        row = session.get(User, user_id)
        if row:
            row.last_login_at = now_iso()


def create_auth_session(
    *,
    user_id: int,
    refresh_token: str,
    expires_at: str,
    auth_method: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    device_id: int | None = None,
) -> dict:
    session_id = str(uuid.uuid4())
    with session_scope() as session:
        row = AuthSession(
            id=session_id,
            user_id=user_id,
            refresh_token_hash=_sha(refresh_token),
            auth_method=auth_method,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            revoked=False,
            expires_at=expires_at,
            created_at=now_iso(),
            last_seen_at=now_iso(),
        )
        session.add(row)
        session.flush()
        return _session_to_dict(row)


def list_auth_sessions(user_id: int, *, include_revoked: bool = False) -> list[dict]:
    with session_scope() as session:
        rows = session.scalars(
            select(AuthSession).where(AuthSession.user_id == user_id).order_by(AuthSession.created_at.desc())
        ).all()
        items = []
        for row in rows:
            if row.revoked and not include_revoked:
                continue
            items.append(_session_to_dict(row))
        return items


def revoke_auth_session(session_id: str, *, user_id: int | None = None) -> bool:
    with session_scope() as session:
        row = session.get(AuthSession, session_id)
        if not row:
            return False
        if user_id is not None and row.user_id != user_id:
            return False
        row.revoked = True
        if row.refresh_token_hash:
            from .db.models import RefreshToken

            token = session.scalar(
                select(RefreshToken).where(RefreshToken.token_hash == row.refresh_token_hash)
            )
            if token:
                token.revoked = True
        return True


def revoke_all_auth_sessions(user_id: int, *, except_session_id: str | None = None) -> int:
    count = 0
    with session_scope() as session:
        rows = session.scalars(select(AuthSession).where(AuthSession.user_id == user_id)).all()
        from .db.models import RefreshToken

        for row in rows:
            if except_session_id and row.id == except_session_id:
                continue
            if row.revoked:
                continue
            row.revoked = True
            count += 1
            if row.refresh_token_hash:
                token = session.scalar(
                    select(RefreshToken).where(RefreshToken.token_hash == row.refresh_token_hash)
                )
                if token:
                    token.revoked = True
    return count


def _session_to_dict(row: AuthSession) -> dict:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "auth_method": row.auth_method,
        "ip_address": row.ip_address,
        "user_agent": row.user_agent,
        "device_id": row.device_id,
        "revoked": bool(row.revoked),
        "expires_at": row.expires_at,
        "created_at": row.created_at,
        "last_seen_at": row.last_seen_at,
    }


def create_trusted_device(
    *,
    user_id: int,
    name: str,
    fingerprint: str | None = None,
) -> dict:
    settings = get_settings()
    raw_token = secrets.token_urlsafe(32)
    expires_at = (
        datetime.now(timezone.utc) + timedelta(days=settings.trusted_device_days)
    ).isoformat()
    with session_scope() as session:
        row = TrustedDevice(
            user_id=user_id,
            name=(name or "Trusted device").strip()[:255],
            device_token_hash=_sha(raw_token),
            fingerprint=(fingerprint or "")[:255] or None,
            last_used_at=now_iso(),
            expires_at=expires_at,
            revoked=False,
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        payload = _device_to_dict(row)
        payload["device_token"] = raw_token
        return payload


def list_trusted_devices(user_id: int) -> list[dict]:
    with session_scope() as session:
        rows = session.scalars(
            select(TrustedDevice)
            .where(TrustedDevice.user_id == user_id)
            .order_by(TrustedDevice.id.desc())
        ).all()
        return [_device_to_dict(row) for row in rows if not row.revoked]


def revoke_trusted_device(device_id: int, *, user_id: int) -> bool:
    with session_scope() as session:
        row = session.get(TrustedDevice, device_id)
        if not row or row.user_id != user_id:
            return False
        row.revoked = True
        return True


def find_valid_trusted_device(user_id: int, device_token: str | None) -> dict | None:
    if not device_token:
        return None
    digest = _sha(device_token)
    with session_scope() as session:
        row = session.scalar(
            select(TrustedDevice).where(
                TrustedDevice.user_id == user_id,
                TrustedDevice.device_token_hash == digest,
            )
        )
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
        row.last_used_at = now_iso()
        return _device_to_dict(row)


def _device_to_dict(row: TrustedDevice) -> dict:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "name": row.name,
        "fingerprint": row.fingerprint,
        "last_used_at": row.last_used_at,
        "expires_at": row.expires_at,
        "revoked": bool(row.revoked),
        "created_at": row.created_at,
    }


def create_password_reset_token(user_id: int) -> str:
    settings = get_settings()
    raw = secrets.token_urlsafe(32)
    expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_ttl_minutes)
    ).isoformat()
    with session_scope() as session:
        session.add(
            PasswordResetToken(
                user_id=user_id,
                token_hash=_sha(raw),
                expires_at=expires_at,
                used=False,
                created_at=now_iso(),
            )
        )
    return raw


def consume_password_reset_token(raw_token: str, new_password: str) -> dict:
    digest = _sha(raw_token)
    with session_scope() as session:
        row = session.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == digest))
        if not row or row.used:
            raise ValueError("Invalid or used reset token")
        try:
            expires = datetime.fromisoformat(row.expires_at)
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < datetime.now(timezone.utc):
                raise ValueError("Reset token expired")
        except ValueError as exc:
            if "expired" in str(exc).lower() or "invalid" in str(exc).lower():
                raise
            raise ValueError("Reset token expired") from exc
        user = session.get(User, row.user_id)
        if not user or not user.is_active:
            raise ValueError("User not found")
        user.password_hash = hash_password(new_password)
        user.must_reset_password = False
        user.failed_login_count = 0
        user.locked_until = None
        row.used = True
        session.flush()
        return _user_to_dict(user)


def get_user_by_oidc(subject: str, provider: str) -> dict | None:
    with session_scope() as session:
        row = session.scalar(
            select(User).where(User.oidc_subject == subject, User.oidc_provider == provider)
        )
        return _user_to_dict(row) if row else None


def upsert_federated_user(
    *,
    email: str | None,
    display_name: str,
    subject: str,
    provider: str,
    auth_provider: str,
    role: str = "citizen",
) -> dict:
    cleaned_email = (email or "").strip().lower() or None
    with session_scope() as session:
        row = session.scalar(
            select(User).where(User.oidc_subject == subject, User.oidc_provider == provider)
        )
        if not row and cleaned_email:
            row = session.scalar(select(User).where(User.email == cleaned_email))
        if row:
            row.display_name = display_name or row.display_name
            if cleaned_email and not row.email:
                row.email = cleaned_email
            row.oidc_subject = subject
            row.oidc_provider = provider
            row.auth_provider = auth_provider
            row.is_active = True
            session.flush()
            return _user_to_dict(row)
        row = User(
            display_name=display_name or cleaned_email or "Federated User",
            email=cleaned_email,
            role=role,
            password_hash=None,
            failed_login_count=0,
            locked_until=None,
            is_active=True,
            mfa_enabled=False,
            mfa_secret=None,
            oidc_subject=subject,
            oidc_provider=provider,
            auth_provider=auth_provider,
            must_reset_password=False,
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        return _user_to_dict(row)


def list_users(*, role: str | None = None, q: str | None = None, limit: int = 100) -> list[dict]:
    with session_scope() as session:
        stmt = select(User).order_by(User.id.desc()).limit(max(1, min(limit, 500)))
        rows = session.scalars(stmt).all()
        items = []
        needle = (q or "").strip().lower()
        for row in rows:
            if role and row.role != role:
                continue
            if needle:
                blob = f"{row.display_name} {row.email or ''} {row.role}".lower()
                if needle not in blob:
                    continue
            items.append(_user_to_dict(row))
        return items


def admin_create_user(
    *,
    display_name: str,
    email: str,
    role: str,
    password: str | None,
    invited_by_user_id: int | None,
    must_reset_password: bool = True,
) -> dict:
    from .core.rbac import Role

    try:
        Role(role)
    except ValueError as exc:
        raise ValueError(f"Invalid role: {role}") from exc
    cleaned = email.strip().lower()
    with session_scope() as session:
        existing = session.scalar(select(User).where(User.email == cleaned))
        if existing:
            raise ValueError("Email already registered")
        temp_password = password or secrets.token_urlsafe(12) + "Aa1"
        row = User(
            display_name=display_name.strip(),
            email=cleaned,
            role=role,
            password_hash=hash_password(temp_password),
            failed_login_count=0,
            locked_until=None,
            is_active=True,
            mfa_enabled=False,
            mfa_secret=None,
            auth_provider="local",
            must_reset_password=must_reset_password,
            invited_by_user_id=invited_by_user_id,
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        payload = _user_to_dict(row)
        payload["temporary_password"] = temp_password
        return payload


def admin_update_user(
    user_id: int,
    *,
    role: str | None = None,
    is_active: bool | None = None,
    display_name: str | None = None,
    must_reset_password: bool | None = None,
) -> dict:
    from .core.rbac import Role

    with session_scope() as session:
        row = session.get(User, user_id)
        if not row:
            raise ValueError("User not found")
        if role is not None:
            try:
                Role(role)
            except ValueError as exc:
                raise ValueError(f"Invalid role: {role}") from exc
            row.role = role
        if is_active is not None:
            row.is_active = bool(is_active)
        if display_name is not None and display_name.strip():
            row.display_name = display_name.strip()
        if must_reset_password is not None:
            row.must_reset_password = bool(must_reset_password)
        session.flush()
        return _user_to_dict(row)


def create_oauth_client(
    *,
    name: str,
    partner_org: str,
    scopes: list[str],
    created_by_user_id: int | None = None,
) -> dict:
    client_id = "msb_oauth_" + secrets.token_urlsafe(12)
    client_secret = secrets.token_urlsafe(32)
    with session_scope() as session:
        row = OAuthClient(
            client_id=client_id,
            client_secret_hash=_sha(client_secret),
            name=name.strip(),
            partner_org=partner_org.strip(),
            scopes_json=json.dumps(scopes, ensure_ascii=True),
            revoked=False,
            created_by_user_id=created_by_user_id,
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        return {
            "id": row.id,
            "client_id": client_id,
            "client_secret": client_secret,
            "name": row.name,
            "partner_org": row.partner_org,
            "scopes": scopes,
            "created_at": row.created_at,
        }


def authenticate_oauth_client(client_id: str, client_secret: str) -> dict | None:
    digest = _sha(client_secret)
    with session_scope() as session:
        row = session.scalar(select(OAuthClient).where(OAuthClient.client_id == client_id))
        if not row or row.revoked:
            return None
        if row.client_secret_hash != digest:
            return None
        return {
            "id": row.id,
            "client_id": row.client_id,
            "name": row.name,
            "partner_org": row.partner_org,
            "scopes": json.loads(row.scopes_json or "[]"),
            "auth_type": "client_credentials",
            "role": "partner",
        }


def set_user_password(user_id: int, password: str) -> dict:
    with session_scope() as session:
        row = session.get(User, user_id)
        if not row:
            raise ValueError("User not found")
        row.password_hash = hash_password(password)
        row.must_reset_password = False
        session.flush()
        return _user_to_dict(row)
