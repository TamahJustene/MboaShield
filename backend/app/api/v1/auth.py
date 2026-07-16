"""JWT auth endpoints - MFA/OIDC-ready skeleton with refresh tokens."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from ...core.config import get_settings
from ...core.security import create_access_token, create_refresh_token, safe_decode_token
from ...repositories import (
    authenticate_user,
    create_user,
    get_user,
    get_user_by_email,
    get_valid_refresh_token,
    revoke_refresh_token,
    store_refresh_token,
    write_audit_log,
)
from ...schemas import AuthLoginIn, AuthRegisterIn, TokenOut, TokenRefreshIn, UserOut
from ..deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua


def _issue_tokens(user: dict) -> TokenOut:
    settings = get_settings()
    access = create_access_token(
        str(user["id"]),
        claims={"role": user["role"], "name": user["display_name"]},
    )
    refresh = create_refresh_token(str(user["id"]))
    expires_at = (datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)).isoformat()
    store_refresh_token(user["id"], refresh, expires_at)
    return TokenOut(
        access_token=access,
        refresh_token=refresh,
        expires_in_minutes=settings.access_token_minutes,
        user=UserOut(**{k: user[k] for k in ("id", "display_name", "email", "role", "created_at", "is_active") if k in user}),
    )


@router.post("/register", response_model=TokenOut)
def register(body: AuthRegisterIn, request: Request):
    if get_user_by_email(body.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = create_user(
        display_name=body.display_name,
        email=body.email.strip().lower(),
        password=body.password,
        role="citizen",
    )
    ip, ua = _client_meta(request)
    write_audit_log(
        action="auth.register",
        actor_user_id=user["id"],
        actor_role=user["role"],
        resource_type="user",
        resource_id=str(user["id"]),
        ip_address=ip,
        user_agent=ua,
    )
    return _issue_tokens(user)


@router.post("/login", response_model=TokenOut)
def login(body: AuthLoginIn, request: Request):
    ip, ua = _client_meta(request)
    try:
        user = authenticate_user(body.email, body.password)
    except ValueError as exc:
        write_audit_log(
            action="auth.login",
            outcome="locked",
            resource_type="user",
            resource_id=body.email,
            ip_address=ip,
            user_agent=ua,
            details={"reason": str(exc)},
        )
        raise HTTPException(status_code=423, detail=str(exc)) from exc

    if not user:
        write_audit_log(
            action="auth.login",
            outcome="failure",
            resource_type="user",
            resource_id=body.email,
            ip_address=ip,
            user_agent=ua,
        )
        raise HTTPException(status_code=401, detail="Invalid email or password")

    write_audit_log(
        action="auth.login",
        actor_user_id=user["id"],
        actor_role=user["role"],
        resource_type="user",
        resource_id=str(user["id"]),
        ip_address=ip,
        user_agent=ua,
    )
    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenOut)
def refresh(body: TokenRefreshIn, request: Request):
    ip, ua = _client_meta(request)
    payload = safe_decode_token(body.refresh_token)
    stored = get_valid_refresh_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh" or not stored:
        write_audit_log(
            action="auth.refresh",
            outcome="failure",
            ip_address=ip,
            user_agent=ua,
        )
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = get_user(stored["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    revoke_refresh_token(body.refresh_token)
    write_audit_log(
        action="auth.refresh",
        actor_user_id=user["id"],
        actor_role=user["role"],
        resource_type="user",
        resource_id=str(user["id"]),
        ip_address=ip,
        user_agent=ua,
    )
    return _issue_tokens(user)


@router.post("/logout")
def logout(body: TokenRefreshIn, request: Request):
    ip, ua = _client_meta(request)
    revoked = revoke_refresh_token(body.refresh_token)
    write_audit_log(
        action="auth.logout",
        outcome="success" if revoked else "failure",
        ip_address=ip,
        user_agent=ua,
    )
    return {"ok": True, "revoked": revoked}


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)):
    return user
