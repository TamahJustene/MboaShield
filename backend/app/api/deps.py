"""API dependency helpers - auth, identity, RBAC."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..core.config import get_settings
from ..core.rbac import has_permission
from ..core.security import safe_decode_token
from ..repositories import get_user

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
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        return None
    user = get_user(user_id)
    if not user or not user.get("is_active", True):
        return None
    return user


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
    ) -> dict | None:
        settings = get_settings()
        if not settings.auth_enforce:
            return get_optional_bearer_user(credentials)

        user = get_optional_bearer_user(credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        if not has_permission(user["role"], permission):
            raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")
        request.state.actor = user
        return user

    return _dependency


LegacyUserId = Annotated[int | None, Depends(resolve_user_id)]
