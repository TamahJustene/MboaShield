"""API dependency helpers - auth, identity, RBAC, partner API keys."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..core.config import get_settings
from ..core.rbac import has_permission
from ..core.security import safe_decode_token, scopes_grant_permission
from ..repositories import authenticate_api_key, get_user

bearer_scheme = HTTPBearer(auto_error=False)


def resolve_user_id(x_mboashield_user_id: str | None = Header(default=None)) -> int | None:
    """Legacy demo identity header - preserved for backward compatibility."""
    if not x_mboashield_user_id:
        return None
    try:
        user_id = int(x_mboashield_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid X-MboaShield-User-Id header") from exc
    if not get_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return user_id


def get_optional_bearer_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict | None:
    if not credentials:
        return None
    payload = safe_decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        return None
    if payload.get("auth_type") == "client_credentials" or str(payload.get("sub", "")).startswith("oauth:"):
        return {
            "id": None,
            "display_name": payload.get("name") or payload.get("sub"),
            "email": None,
            "role": "partner",
            "auth_type": "client_credentials",
            "scopes": payload.get("scopes") or [],
            "partner_org": payload.get("partner_org"),
            "is_active": True,
            "mfa_enabled": False,
        }
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        return None
    user = get_user(user_id)
    if not user or not user.get("is_active", True):
        return None
    user = dict(user)
    user["auth_type"] = "jwt"
    user["token_jti"] = payload.get("jti")
    return user


def get_optional_api_key_actor(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> dict | None:
    if not x_api_key:
        return None
    return authenticate_api_key(x_api_key)


def get_optional_actor(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict | None:
    user = get_optional_bearer_user(credentials)
    if user:
        return user
    return get_optional_api_key_actor(x_api_key)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict:
    user = get_optional_bearer_user(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_permission(permission: str):
    """Factory dependency. When AUTH_ENFORCE is false, allows all (demo continuity)."""

    def _dependency(
        request: Request,
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict | None:
        settings = get_settings()
        actor = get_optional_bearer_user(credentials) or get_optional_api_key_actor(x_api_key)

        if not settings.auth_enforce:
            return actor

        if not actor:
            raise HTTPException(status_code=401, detail="Authentication required")

        if actor.get("auth_type") == "api_key":
            if not scopes_grant_permission(actor.get("scopes") or [], permission):
                raise HTTPException(status_code=403, detail=f"API key missing scope/permission: {permission}")
        elif actor.get("auth_type") == "client_credentials":
            if not scopes_grant_permission(actor.get("scopes") or [], permission):
                raise HTTPException(status_code=403, detail=f"OAuth client missing scope/permission: {permission}")
        elif not has_permission(actor["role"], permission):
            raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")

        request.state.actor = actor
        return actor

    return _dependency


LegacyUserId = Annotated[int | None, Depends(resolve_user_id)]
