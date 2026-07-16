from __future__ import annotations

import hashlib
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import pyotp
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEFAULT_JWT_SECRET = "change-me-in-production-mboashield"
API_KEY_PREFIX = "msb_"

SCOPE_TO_PERMISSIONS = {
    "checks:create": {"checks:create"},
    "incidents:create": {"incidents:create"},
    "incidents:review": {"incidents:review"},
    "history:read_all": {"history:read_all"},
    "analytics:read": {"history:read_all", "audit:read"},
    "institutions:read": {"institutions:read"},
    "institutions:manage": {"institutions:manage"},
    "partners:manage": {"partners:manage", "system:admin"},
}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    return pwd_context.verify(plain, hashed)


def validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Za-z]", password):
        raise ValueError("Password must include a letter")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must include a number")


def production_security_warnings() -> list[str]:
    settings = get_settings()
    warnings: list[str] = []
    if settings.environment.lower() in {"prod", "production"}:
        if settings.jwt_secret == DEFAULT_JWT_SECRET:
            warnings.append("JWT_SECRET is using the insecure default value")
        if not settings.auth_enforce:
            warnings.append("AUTH_ENFORCE is false in a production environment")
        if settings.cors_origins.strip() == "*":
            warnings.append("CORS_ORIGINS allows all origins in production")
    return warnings


def create_access_token(subject: str, claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes),
        "iat": datetime.now(timezone.utc),
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    settings = get_settings()
    payload = {
        "sub": subject,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_mfa_challenge_token(user_id: int) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "type": "mfa_challenge",
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def safe_decode_token(token: str) -> dict[str, Any] | None:
    try:
        return decode_token(token)
    except JWTError:
        return None


def generate_mfa_secret() -> str:
    return pyotp.random_base32()


def build_otpauth_uri(*, secret: str, email: str, issuer: str = "MboaShield") -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email or "user", issuer_name=issuer)


def verify_totp(secret: str | None, code: str) -> bool:
    if not secret:
        return False
    totp = pyotp.TOTP(secret)
    return bool(totp.verify(code.strip(), valid_window=1))


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    raw = API_KEY_PREFIX + secrets.token_urlsafe(32)
    return raw, raw[:12], hash_api_key(raw)


def scopes_grant_permission(scopes: list[str], permission: str) -> bool:
    granted: set[str] = set()
    for scope in scopes:
        granted.update(SCOPE_TO_PERMISSIONS.get(scope, set()))
        granted.add(scope)
    return permission in granted


def oidc_providers() -> list[dict[str, Any]]:
    settings = get_settings()
    providers = []
    if settings.oidc_issuer and settings.oidc_client_id:
        providers.append(
            {
                "id": settings.oidc_provider_id,
                "name": settings.oidc_provider_name,
                "issuer": settings.oidc_issuer,
                "client_id": settings.oidc_client_id,
                "scopes": settings.oidc_scopes,
                "configured": bool(settings.oidc_client_secret),
                "authorize_path": f"/api/v1/auth/oidc/{settings.oidc_provider_id}/authorize",
                "callback_path": f"/api/v1/auth/oidc/{settings.oidc_provider_id}/callback",
                "status": "ready" if settings.oidc_client_secret else "missing_client_secret",
            }
        )
    return providers


def build_oidc_authorize_url(*, state: str, redirect_uri: str) -> str:
    settings = get_settings()
    if not settings.oidc_issuer or not settings.oidc_client_id:
        raise ValueError("OIDC provider is not configured")
    base = settings.oidc_issuer.rstrip("/") + "/authorize"
    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.oidc_client_id,
            "redirect_uri": redirect_uri,
            "scope": settings.oidc_scopes,
            "state": state,
        }
    )
    return f"{base}?{query}"
