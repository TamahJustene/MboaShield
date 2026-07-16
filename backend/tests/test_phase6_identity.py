"""Phase 6 enterprise identity tests."""

from __future__ import annotations

import base64

import pyotp


def test_password_reset_flow(client, monkeypatch):
    test_client, _ = client
    monkeypatch.setenv("PASSWORD_RESET_RETURN_TOKEN", "true")
    from backend.app.core.config import get_settings

    get_settings.cache_clear()

    test_client.post(
        "/api/v1/auth/register",
        json={"display_name": "Reset User", "email": "reset@mboashield.cm", "password": "SecurePass1"},
    )
    forgot = test_client.post("/api/v1/auth/password/forgot", json={"email": "reset@mboashield.cm"})
    assert forgot.status_code == 200
    token = forgot.json()["reset_token"]
    reset = test_client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": "SecurePass2"},
    )
    assert reset.status_code == 200
    login = test_client.post(
        "/api/v1/auth/login",
        json={"email": "reset@mboashield.cm", "password": "SecurePass2"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_sessions_and_admin_users(client):
    test_client, _ = client
    registered = test_client.post(
        "/api/v1/auth/register",
        json={"display_name": "Admin", "email": "admin6@mboashield.cm", "password": "SecurePass1"},
    ).json()
    headers = {"Authorization": f"Bearer {registered['access_token']}"}

    # promote via admin API (soft auth allows without users:manage)
    created = test_client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "display_name": "Analyst Two",
            "email": "analyst2@mboashield.cm",
            "role": "analyst",
        },
    )
    assert created.status_code == 200
    assert created.json()["temporary_password"]
    assert created.json()["user"]["role"] == "analyst"

    listed = test_client.get("/api/v1/admin/users", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["count"] >= 2

    sessions = test_client.get("/api/v1/auth/sessions", headers=headers)
    assert sessions.status_code == 200
    assert sessions.json()["count"] >= 1
    session_id = sessions.json()["sessions"][0]["id"]
    revoked = test_client.post(
        "/api/v1/auth/sessions/revoke",
        headers=headers,
        json={"session_id": session_id},
    )
    assert revoked.status_code == 200
    assert revoked.json()["ok"] is True


def test_oauth_client_credentials(client):
    test_client, _ = client
    created = test_client.post(
        "/api/v1/oauth/clients",
        json={
            "name": "Telco Bridge",
            "partner_org": "MTN CM",
            "scopes": ["checks:create", "institutions:read"],
        },
    )
    assert created.status_code == 200
    client_id = created.json()["client_id"]
    client_secret = created.json()["client_secret"]

    token = test_client.post(
        "/api/v1/oauth/token",
        json={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    assert token.status_code == 200
    assert token.json()["access_token"]
    assert token.json()["token_type"] == "bearer"


def test_oidc_callback_exchange(client, monkeypatch):
    test_client, _ = client
    monkeypatch.setenv("OIDC_ENABLED", "true")
    monkeypatch.setenv("OIDC_ISSUER", "https://idp.example.cm/realms/mboa")
    monkeypatch.setenv("OIDC_CLIENT_ID", "mboashield")
    monkeypatch.setenv("OIDC_CLIENT_SECRET", "secret")
    from backend.app.core.config import get_settings

    get_settings.cache_clear()

    def fake_exchange(*, code: str, redirect_uri: str):
        assert code == "auth-code-1"
        return {
            "token_response": {"access_token": "x"},
            "claims": {"sub": "oidc-sub-1", "email": "sso@mboashield.cm", "name": "SSO User"},
            "subject": "oidc-sub-1",
            "email": "sso@mboashield.cm",
            "display_name": "SSO User",
        }

    monkeypatch.setattr(
        "backend.app.api.v1.auth.exchange_oidc_code",
        fake_exchange,
    )
    response = test_client.post(
        "/api/v1/auth/oidc/national-id/callback",
        json={"code": "auth-code-1", "state": "abc"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mfa_required"] is False
    assert body["access_token"]
    assert body["user"]["email"] == "sso@mboashield.cm"
    assert body["user"]["auth_provider"] == "oidc"


def test_saml_acs_unsigned_allowed(client, monkeypatch):
    test_client, _ = client
    monkeypatch.setenv("SAML_ENABLED", "true")
    monkeypatch.setenv("SAML_ALLOW_UNSIGNED", "true")
    from backend.app.core.config import get_settings

    get_settings.cache_clear()

    assertion = """<?xml version="1.0"?>
    <samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
      <saml:Assertion>
        <saml:Subject>
          <saml:NameID>saml.user@mboashield.cm</saml:NameID>
        </saml:Subject>
        <saml:AttributeStatement>
          <saml:Attribute Name="email">
            <saml:AttributeValue>saml.user@mboashield.cm</saml:AttributeValue>
          </saml:Attribute>
          <saml:Attribute Name="displayName">
            <saml:AttributeValue>SAML User</saml:AttributeValue>
          </saml:Attribute>
        </saml:AttributeStatement>
      </saml:Assertion>
    </samlp:Response>
    """.strip()
    encoded = base64.b64encode(assertion.encode("utf-8")).decode("ascii")
    meta = test_client.get("/api/v1/auth/saml/metadata")
    assert meta.status_code == 200
    assert "EntityDescriptor" in meta.text

    acs = test_client.post("/api/v1/auth/saml/acs", json={"SAMLResponse": encoded})
    assert acs.status_code == 200
    assert acs.json()["access_token"]
    assert acs.json()["user"]["auth_provider"] == "saml"


def test_trusted_device_skips_mfa(client):
    test_client, _ = client
    registered = test_client.post(
        "/api/v1/auth/register",
        json={"display_name": "Device User", "email": "device@mboashield.cm", "password": "SecurePass1"},
    ).json()
    headers = {"Authorization": f"Bearer {registered['access_token']}"}
    setup = test_client.post("/api/v1/auth/mfa/setup", headers=headers).json()
    code = pyotp.TOTP(setup["secret"]).now()
    test_client.post("/api/v1/auth/mfa/enable", headers=headers, json={"code": code})

    login = test_client.post(
        "/api/v1/auth/login",
        json={"email": "device@mboashield.cm", "password": "SecurePass1"},
    ).json()
    assert login["mfa_required"] is True
    verify = test_client.post(
        "/api/v1/auth/mfa/verify",
        json={
            "code": pyotp.TOTP(setup["secret"]).now(),
            "mfa_token": login["mfa_token"],
            "trust_device": True,
            "device_name": "pytest",
        },
    ).json()
    device_token = verify["device_token"]
    assert device_token

    again = test_client.post(
        "/api/v1/auth/login",
        json={
            "email": "device@mboashield.cm",
            "password": "SecurePass1",
            "device_token": device_token,
        },
    )
    assert again.status_code == 200
    assert again.json()["mfa_required"] is False
    assert again.json()["access_token"]


def test_security_status_phase6_flags(client):
    test_client, _ = client
    status = test_client.get("/api/v1/auth/security-status").json()
    assert status["sessions_ready"] is True
    assert status["trusted_devices_ready"] is True
    assert status["admin_users_ready"] is True
    assert status["password_recovery_ready"] is True
    assert "deployment_profile" in status
