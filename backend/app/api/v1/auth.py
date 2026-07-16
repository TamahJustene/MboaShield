"""JWT auth + MFA + OIDC/SAML/LDAP + sessions/devices/password recovery."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from ...core.config import get_settings
from ...core.security import (
    build_oidc_authorize_url,
    create_access_token,
    create_mfa_challenge_token,
    create_refresh_token,
    generate_mfa_secret,
    build_otpauth_uri,
    oidc_providers,
    production_security_warnings,
    safe_decode_token,
    validate_password_strength,
    verify_totp,
)
from ...identity_store import (
    create_auth_session,
    create_password_reset_token,
    create_trusted_device,
    consume_password_reset_token,
    ensure_default_tenant,
    find_valid_trusted_device,
    list_auth_sessions,
    list_trusted_devices,
    revoke_all_auth_sessions,
    revoke_auth_session,
    revoke_trusted_device,
    touch_user_login,
    upsert_federated_user,
    write_auth_event,
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
    DeviceTrustIn,
    LdapLoginIn,
    MfaCodeIn,
    MfaSetupOut,
    OidcCallbackIn,
    PasswordForgotIn,
    PasswordResetIn,
    SessionRevokeIn,
    TokenOut,
    TokenRefreshIn,
    UserOut,
)
from ...services.identity_federation import (
    build_saml_metadata_xml,
    exchange_oidc_code,
    ldap_authenticate,
    parse_saml_response,
    validate_password_policy,
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
        auth_provider=user.get("auth_provider") or "local",
        must_reset_password=bool(user.get("must_reset_password", False)),
        last_login_at=user.get("last_login_at"),
    )


def _issue_tokens(
    user: dict,
    *,
    request: Request | None = None,
    auth_method: str = "password",
    device_id: int | None = None,
) -> TokenOut:
    settings = get_settings()
    access = create_access_token(
        str(user["id"]),
        claims={
            "role": user["role"],
            "name": user["display_name"],
            "mfa": bool(user.get("mfa_enabled")),
            "auth_method": auth_method,
        },
    )
    refresh = create_refresh_token(str(user["id"]))
    expires_at = (datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)).isoformat()
    store_refresh_token(user["id"], refresh, expires_at)
    ip = ua = None
    if request is not None:
        ip, ua = _client_meta(request)
    session = create_auth_session(
        user_id=user["id"],
        refresh_token=refresh,
        expires_at=expires_at,
        auth_method=auth_method,
        ip_address=ip,
        user_agent=ua,
        device_id=device_id,
    )
    touch_user_login(user["id"])
    return TokenOut(
        access_token=access,
        refresh_token=refresh,
        expires_in_minutes=settings.access_token_minutes,
        user=_user_out(user),
        session_id=session["id"],
    )


def _session_from_tokens(tokens: TokenOut) -> AuthSessionOut:
    return AuthSessionOut(
        mfa_required=False,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type="bearer",
        expires_in_minutes=tokens.expires_in_minutes,
        user=tokens.user,
        session_id=tokens.session_id,
    )


def _maybe_mfa_challenge(
    user: dict,
    *,
    request: Request,
    device_token: str | None = None,
) -> AuthSessionOut | None:
    settings = get_settings()
    ip, ua = _client_meta(request)
    trusted = find_valid_trusted_device(user["id"], device_token)
    if (
        user.get("mfa_enabled")
        and settings.trusted_device_skip_mfa
        and trusted
    ):
        write_auth_event(
            event_type="auth.trusted_device_skip_mfa",
            user_id=user["id"],
            ip_address=ip,
            user_agent=ua,
            details={"device_id": trusted["id"]},
        )
        return None

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

    if settings.mfa_enforce and user.get("role") in settings.mfa_roles():
        write_auth_event(
            event_type="auth.mfa_required_not_enrolled",
            outcome="blocked",
            user_id=user["id"],
            ip_address=ip,
            user_agent=ua,
        )
        raise HTTPException(
            status_code=403,
            detail="MFA enrollment is required for this role before sign-in can complete",
        )
    return None


@router.get("/security-status")
def security_status():
    settings = get_settings()
    tenant = ensure_default_tenant()
    return {
        "environment": settings.environment,
        "deployment_profile": settings.deployment_profile,
        "tenant": tenant,
        "auth_enforce": settings.auth_enforce,
        "mfa_required_roles": sorted(settings.mfa_roles()),
        "mfa_enforce": settings.mfa_enforce,
        "oidc_providers": oidc_providers(),
        "oidc_enabled": settings.oidc_enabled,
        "saml_enabled": settings.saml_enabled,
        "ldap_enabled": settings.ldap_enabled,
        "warnings": production_security_warnings(),
        "oauth2_ready": True,
        "oidc_ready": bool(settings.oidc_issuer and settings.oidc_client_id and settings.oidc_client_secret),
        "saml_ready": bool(settings.saml_enabled and (settings.saml_idp_x509_cert or settings.saml_allow_unsigned)),
        "ldap_ready": bool(settings.ldap_enabled and settings.ldap_server_uri),
        "mfa_ready": True,
        "partner_api_keys_ready": True,
        "sessions_ready": True,
        "trusted_devices_ready": True,
        "password_recovery_ready": True,
        "admin_users_ready": True,
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
    write_auth_event(event_type="auth.register", user_id=user["id"], ip_address=ip, user_agent=ua)
    return _issue_tokens(user, request=request, auth_method="password")


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

    challenge = _maybe_mfa_challenge(user, request=request, device_token=body.device_token)
    if challenge:
        return challenge

    settings = get_settings()
    if user.get("role") in settings.mfa_roles() and not user.get("mfa_enabled") and not settings.mfa_enforce:
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
    trusted = find_valid_trusted_device(user["id"], body.device_token)
    return _session_from_tokens(
        _issue_tokens(
            user,
            request=request,
            auth_method="password",
            device_id=trusted["id"] if trusted else None,
        )
    )


@router.post("/ldap/login", response_model=AuthSessionOut)
def ldap_login(body: LdapLoginIn, request: Request):
    settings = get_settings()
    if not settings.ldap_enabled:
        raise HTTPException(status_code=404, detail="LDAP login is disabled")
    ip, ua = _client_meta(request)
    try:
        profile = ldap_authenticate(body.username, body.password)
    except Exception as exc:
        write_auth_event(
            event_type="auth.ldap_login",
            outcome="failure",
            ip_address=ip,
            user_agent=ua,
            details={"reason": str(exc)},
        )
        raise HTTPException(status_code=401, detail="LDAP authentication failed") from exc

    user = upsert_federated_user(
        email=profile["email"],
        display_name=profile["display_name"],
        subject=profile["subject"],
        provider="ldap",
        auth_provider="ldap",
        role=profile.get("role") or settings.ldap_default_role,
    )
    challenge = _maybe_mfa_challenge(user, request=request, device_token=body.device_token)
    if challenge:
        return challenge
    write_audit_log(
        action="auth.ldap_login",
        actor_user_id=user["id"],
        actor_role=user["role"],
        resource_type="user",
        resource_id=str(user["id"]),
        ip_address=ip,
        user_agent=ua,
    )
    return _session_from_tokens(_issue_tokens(user, request=request, auth_method="ldap"))


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
    tokens = _issue_tokens(user, request=request, auth_method="password+mfa")
    session = _session_from_tokens(tokens)
    if body.trust_device:
        device = create_trusted_device(
            user_id=user["id"],
            name=body.device_name or "Trusted device",
            fingerprint=ua,
        )
        session.device_token = device["device_token"]
        session.device_id = device["id"]
    return session


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
    if not settings.oidc_enabled:
        raise HTTPException(status_code=404, detail="OIDC is disabled")
    if provider_id != settings.oidc_provider_id:
        raise HTTPException(status_code=404, detail="OIDC provider not found")
    try:
        state = secrets.token_urlsafe(16)
        nonce = secrets.token_urlsafe(12)
        url = build_oidc_authorize_url(
            state=state,
            redirect_uri=settings.oidc_redirect_uri,
            nonce=nonce,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "provider_id": provider_id,
        "authorize_url": url,
        "state": state,
        "nonce": nonce,
        "redirect_uri": settings.oidc_redirect_uri,
    }


@router.post("/oidc/{provider_id}/callback", response_model=AuthSessionOut)
def oidc_callback(provider_id: str, body: OidcCallbackIn, request: Request):
    settings = get_settings()
    if not settings.oidc_enabled:
        raise HTTPException(status_code=404, detail="OIDC is disabled")
    if provider_id != settings.oidc_provider_id:
        raise HTTPException(status_code=404, detail="OIDC provider not found")
    if not body.code:
        raise HTTPException(status_code=400, detail="Authorization code is required")
    try:
        exchanged = exchange_oidc_code(code=body.code, redirect_uri=settings.oidc_redirect_uri)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user = upsert_federated_user(
        email=exchanged.get("email"),
        display_name=exchanged["display_name"],
        subject=exchanged["subject"],
        provider=provider_id,
        auth_provider="oidc",
        role=settings.oidc_default_role,
    )
    challenge = _maybe_mfa_challenge(user, request=request, device_token=body.device_token)
    if challenge:
        return challenge
    ip, ua = _client_meta(request)
    write_audit_log(
        action="auth.oidc_login",
        actor_user_id=user["id"],
        actor_role=user["role"],
        resource_type="user",
        resource_id=str(user["id"]),
        ip_address=ip,
        user_agent=ua,
        details={"provider": provider_id},
    )
    return _session_from_tokens(_issue_tokens(user, request=request, auth_method="oidc"))


@router.get("/saml/metadata")
def saml_metadata():
    settings = get_settings()
    if not settings.saml_enabled:
        raise HTTPException(status_code=404, detail="SAML is disabled")
    xml = build_saml_metadata_xml()
    return Response(content=xml, media_type="application/samlmetadata+xml")


@router.post("/saml/acs", response_model=AuthSessionOut)
async def saml_acs(request: Request):
    settings = get_settings()
    if not settings.saml_enabled:
        raise HTTPException(status_code=404, detail="SAML is disabled")
    content_type = (request.headers.get("content-type") or "").lower()
    saml_b64 = ""
    relay_state = ""
    if "application/json" in content_type:
        try:
            payload = await request.json()
            saml_b64 = payload.get("SAMLResponse") or payload.get("saml_response") or ""
            relay_state = payload.get("RelayState") or ""
        except Exception:
            saml_b64 = ""
    else:
        form = await request.form()
        saml_b64 = str(form.get("SAMLResponse") or "")
        relay_state = str(form.get("RelayState") or "")
    if not saml_b64:
        raise HTTPException(status_code=400, detail="SAMLResponse is required")
    try:
        assertion = parse_saml_response(saml_b64)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user = upsert_federated_user(
        email=assertion.get("email"),
        display_name=assertion["display_name"],
        subject=f"saml:{assertion['subject']}",
        provider="saml",
        auth_provider="saml",
        role=settings.saml_default_role,
    )
    challenge = _maybe_mfa_challenge(user, request=request)
    if challenge:
        return challenge
    ip, ua = _client_meta(request)
    write_audit_log(
        action="auth.saml_login",
        actor_user_id=user["id"],
        actor_role=user["role"],
        resource_type="user",
        resource_id=str(user["id"]),
        ip_address=ip,
        user_agent=ua,
        details={"relay_state": relay_state or None},
    )
    return _session_from_tokens(_issue_tokens(user, request=request, auth_method="saml"))


@router.post("/password/forgot")
def password_forgot(body: PasswordForgotIn, request: Request):
    settings = get_settings()
    ip, ua = _client_meta(request)
    user = get_user_by_email(body.email.strip().lower())
    response: dict = {"ok": True, "message": "If the account exists, a reset token was issued"}
    if user:
        token = create_password_reset_token(user["id"])
        write_auth_event(
            event_type="auth.password_forgot",
            user_id=user["id"],
            ip_address=ip,
            user_agent=ua,
        )
        if settings.password_reset_return_token:
            response["reset_token"] = token
    return response


@router.post("/password/reset", response_model=UserOut)
def password_reset(body: PasswordResetIn, request: Request):
    try:
        validate_password_policy(body.new_password)
        user = consume_password_reset_token(body.token, body.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ip, ua = _client_meta(request)
    write_audit_log(
        action="auth.password_reset",
        actor_user_id=user["id"],
        actor_role=user["role"],
        resource_type="user",
        resource_id=str(user["id"]),
        ip_address=ip,
        user_agent=ua,
    )
    revoke_all_auth_sessions(user["id"])
    return _user_out(user)


@router.get("/sessions")
def sessions(user: dict = Depends(get_current_user)):
    return {"sessions": list_auth_sessions(user["id"]), "count": len(list_auth_sessions(user["id"]))}


@router.post("/sessions/revoke")
def sessions_revoke(body: SessionRevokeIn, request: Request, user: dict = Depends(get_current_user)):
    ip, ua = _client_meta(request)
    if body.revoke_all:
        count = revoke_all_auth_sessions(user["id"], except_session_id=body.except_session_id)
        write_auth_event(
            event_type="auth.sessions_revoke_all",
            user_id=user["id"],
            ip_address=ip,
            user_agent=ua,
            details={"count": count},
        )
        return {"ok": True, "revoked": count}
    if not body.session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    ok = revoke_auth_session(body.session_id, user_id=user["id"])
    write_auth_event(
        event_type="auth.session_revoke",
        outcome="success" if ok else "failure",
        user_id=user["id"],
        ip_address=ip,
        user_agent=ua,
        details={"session_id": body.session_id},
    )
    return {"ok": ok}


@router.get("/devices")
def devices(user: dict = Depends(get_current_user)):
    items = list_trusted_devices(user["id"])
    return {"devices": items, "count": len(items)}


@router.post("/devices/trust")
def devices_trust(body: DeviceTrustIn, request: Request, user: dict = Depends(get_current_user)):
    ip, ua = _client_meta(request)
    device = create_trusted_device(user_id=user["id"], name=body.name, fingerprint=body.fingerprint or ua)
    write_auth_event(
        event_type="auth.device_trust",
        user_id=user["id"],
        ip_address=ip,
        user_agent=ua,
        details={"device_id": device["id"]},
    )
    return device


@router.delete("/devices/{device_id}")
def devices_revoke(device_id: int, request: Request, user: dict = Depends(get_current_user)):
    ok = revoke_trusted_device(device_id, user_id=user["id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Device not found")
    ip, ua = _client_meta(request)
    write_auth_event(
        event_type="auth.device_revoke",
        user_id=user["id"],
        ip_address=ip,
        user_agent=ua,
        details={"device_id": device_id},
    )
    return {"ok": True}


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
    return _issue_tokens(user, request=request, auth_method="refresh")


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
