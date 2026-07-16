"""JWT auth + MFA + OIDC-ready identity endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request

from ...core.config import get_settings
from ...core.security import (
    build_oidc_authorize_url,
    build_otpauth_uri,
    create_access_token,
    create_mfa_challenge_token,
    create_refresh_token,
    generate_mfa_secret,
    oidc_providers,
    production_security_warnings,
    safe_decode_token,
    validate_password_strength,
    verify_totp,
)
from ...repositories import (
    authenticate_user,
    begin_mfa_setup,
    create_user,
    disable_mfa,
    enable_mfa,
    get_user,
    get_user_by_email,
    get_user_mfa_secret,
    get_valid_refresh_token,
    revoke_refresh_token,
    store_refresh_token,
    write_audit_log,
)
from ...schemas import (
    AuthLoginIn,
    AuthRegisterIn,
    AuthSessionOut,
    MfaCodeIn,
    MfaSetupOut,
    OidcCallbackIn,
    TokenOut,
    TokenRefreshIn,
    UserOut,
)
from ..deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua


def _user_out(user: dict) -> UserOut:
    return UserOut(
        id=user["id"],
        display_name=user["display_name"],
        email=user.get("email"),
        role=user["role"],
        created_at=user["created_at"],
        is_active=bool(user.get("is_active", True)),
        mfa_enabled=bool(user.get("mfa_enabled", False)),
    )


def _issue_tokens(user: dict) -> TokenOut:
    settings = get_settings()
    access = create_access_token(
        str(user["id"]),
        claims={"role": user["role"], "name": user["display_name"], "mfa": bool(user.get("mfa_enabled"))},
    )
    refresh = create_refresh_token(str(user["id"]))
    expires_at = (datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)).isoformat()
    store_refresh_token(user["id"], refresh, expires_at)
    return TokenOut(
        access_token=access,
        refresh_token=refresh,
        expires_in_minutes=settings.access_token_minutes,
        user=_user_out(user),
    )


def _session_from_tokens(tokens: TokenOut) -> AuthSessionOut:
    return AuthSessionOut(
        mfa_required=False,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type="bearer",
        expires_in_minutes=tokens.expires_in_minutes,
        user=tokens.user,
    )


@router.get("/security-status")
def security_status():
    settings = get_settings()
    return {
        "environment": settings.environment,
        "auth_enforce": settings.auth_enforce,
        "mfa_required_roles": sorted(settings.mfa_roles()),
        "oidc_providers": oidc_providers(),
        "warnings": production_security_warnings(),
        "oauth2_ready": True,
        "oidc_ready": bool(settings.oidc_issuer and settings.oidc_client_id),
        "mfa_ready": True,
        "partner_api_keys_ready": True,
    }


@router.post("/register", response_model=TokenOut)
def register(body: AuthRegisterIn, request: Request):
    try:
        validate_password_strength(body.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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


@router.post("/login", response_model=AuthSessionOut)
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

    settings = get_settings()
    require_mfa = user.get("mfa_enabled") or user.get("role") in settings.mfa_roles()
    if user.get("mfa_enabled"):
        write_audit_log(
            action="auth.login",
            outcome="mfa_challenge",
            actor_user_id=user["id"],
            actor_role=user["role"],
            resource_type="user",
            resource_id=str(user["id"]),
            ip_address=ip,
            user_agent=ua,
        )
        return AuthSessionOut(
            mfa_required=True,
            mfa_token=create_mfa_challenge_token(user["id"]),
            token_type="mfa_challenge",
            user=_user_out(user),
        )

    if require_mfa and not user.get("mfa_enabled"):
        # Policy hint only; do not block until MFA is enrolled.
        write_audit_log(
            action="auth.login",
            outcome="success_mfa_recommended",
            actor_user_id=user["id"],
            actor_role=user["role"],
            resource_type="user",
            resource_id=str(user["id"]),
            ip_address=ip,
            user_agent=ua,
        )
    else:
        write_audit_log(
            action="auth.login",
            actor_user_id=user["id"],
            actor_role=user["role"],
            resource_type="user",
            resource_id=str(user["id"]),
            ip_address=ip,
            user_agent=ua,
        )
    return _session_from_tokens(_issue_tokens(user))


@router.post("/mfa/setup", response_model=MfaSetupOut)
def mfa_setup(user: dict = Depends(get_current_user)):
    secret = generate_mfa_secret()
    begin_mfa_setup(user["id"], secret)
    uri = build_otpauth_uri(secret=secret, email=user.get("email") or user["display_name"])
    return MfaSetupOut(secret=secret, otpauth_uri=uri, mfa_enabled=False)


@router.post("/mfa/enable", response_model=UserOut)
def mfa_enable(body: MfaCodeIn, request: Request, user: dict = Depends(get_current_user)):
    secret = get_user_mfa_secret(user["id"])
    if not verify_totp(secret, body.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    updated = enable_mfa(user["id"])
    ip, ua = _client_meta(request)
    write_audit_log(
        action="auth.mfa_enable",
        actor_user_id=user["id"],
        actor_role=user["role"],
        resource_type="user",
        resource_id=str(user["id"]),
        ip_address=ip,
        user_agent=ua,
    )
    return _user_out(updated)


@router.post("/mfa/verify", response_model=AuthSessionOut)
def mfa_verify(body: MfaCodeIn, request: Request):
    if not body.mfa_token:
        raise HTTPException(status_code=400, detail="mfa_token is required")
    payload = safe_decode_token(body.mfa_token)
    if not payload or payload.get("type") != "mfa_challenge":
        raise HTTPException(status_code=401, detail="Invalid MFA challenge token")
    user_id = int(payload["sub"])
    secret = get_user_mfa_secret(user_id)
    if not verify_totp(secret, body.code):
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    ip, ua = _client_meta(request)
    write_audit_log(
        action="auth.mfa_verify",
        actor_user_id=user["id"],
        actor_role=user["role"],
        resource_type="user",
        resource_id=str(user["id"]),
        ip_address=ip,
        user_agent=ua,
    )
    return _session_from_tokens(_issue_tokens(user))


@router.post("/mfa/disable", response_model=UserOut)
def mfa_disable(body: MfaCodeIn, request: Request, user: dict = Depends(get_current_user)):
    secret = get_user_mfa_secret(user["id"])
    if user.get("mfa_enabled") and not verify_totp(secret, body.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    updated = disable_mfa(user["id"])
    ip, ua = _client_meta(request)
    write_audit_log(
        action="auth.mfa_disable",
        actor_user_id=user["id"],
        actor_role=user["role"],
        resource_type="user",
        resource_id=str(user["id"]),
        ip_address=ip,
        user_agent=ua,
    )
    return _user_out(updated)


@router.get("/oidc/providers")
def list_oidc_providers():
    return {"providers": oidc_providers(), "count": len(oidc_providers()), "oauth2_support": True}


@router.get("/oidc/{provider_id}/authorize")
def oidc_authorize(provider_id: str, request: Request):
    settings = get_settings()
    if provider_id != settings.oidc_provider_id:
        raise HTTPException(status_code=404, detail="OIDC provider not found")
    try:
        state = secrets.token_urlsafe(16)
        url = build_oidc_authorize_url(state=state, redirect_uri=settings.oidc_redirect_uri)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "provider_id": provider_id,
        "authorize_url": url,
        "state": state,
        "redirect_uri": settings.oidc_redirect_uri,
        "note": "Complete token exchange via callback once the IdP is connected.",
    }


@router.post("/oidc/{provider_id}/callback")
def oidc_callback(provider_id: str, body: OidcCallbackIn):
    settings = get_settings()
    if provider_id != settings.oidc_provider_id:
        raise HTTPException(status_code=404, detail="OIDC provider not found")
    if not settings.oidc_issuer or not settings.oidc_client_id or not settings.oidc_client_secret:
        raise HTTPException(
            status_code=501,
            detail="OIDC provider is configured incompletely. Set OIDC_ISSUER, OIDC_CLIENT_ID, and OIDC_CLIENT_SECRET.",
        )
    return {
        "status": "accepted",
        "provider_id": provider_id,
        "code_received": bool(body.code),
        "next_step": "Exchange authorization code with the IdP token endpoint and map claims to a MboaShield user.",
        "ready": True,
    }


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
    return _user_out(user)
