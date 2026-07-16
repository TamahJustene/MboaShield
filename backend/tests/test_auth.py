from __future__ import annotations

import pyotp


def test_register_login_refresh_logout(client):
    test_client, _ = client

    registered = test_client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Analyst One",
            "email": "analyst@mboashield.cm",
            "password": "SecurePass1",
        },
    )
    assert registered.status_code == 200
    tokens = registered.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["user"]["email"] == "analyst@mboashield.cm"

    me = test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["display_name"] == "Analyst One"

    login = test_client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@mboashield.cm", "password": "SecurePass1"},
    )
    assert login.status_code == 200
    assert login.json()["mfa_required"] is False
    assert login.json()["access_token"]
    refreshed = test_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    )
    assert refreshed.status_code == 200

    logout = test_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refreshed.json()["refresh_token"]},
    )
    assert logout.status_code == 200
    assert logout.json()["revoked"] is True


def test_bad_login_rejected(client):
    test_client, _ = client
    test_client.post(
        "/api/v1/auth/register",
        json={"display_name": "User", "email": "user@mboashield.cm", "password": "SecurePass1"},
    )
    response = test_client.post(
        "/api/v1/auth/login",
        json={"email": "user@mboashield.cm", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_mfa_setup_enable_and_challenge(client):
    test_client, _ = client
    registered = test_client.post(
        "/api/v1/auth/register",
        json={"display_name": "MFA User", "email": "mfa@mboashield.cm", "password": "SecurePass1"},
    ).json()
    headers = {"Authorization": f"Bearer {registered['access_token']}"}

    setup = test_client.post("/api/v1/auth/mfa/setup", headers=headers)
    assert setup.status_code == 200
    secret = setup.json()["secret"]
    code = pyotp.TOTP(secret).now()

    enabled = test_client.post("/api/v1/auth/mfa/enable", headers=headers, json={"code": code})
    assert enabled.status_code == 200
    assert enabled.json()["mfa_enabled"] is True

    login = test_client.post(
        "/api/v1/auth/login",
        json={"email": "mfa@mboashield.cm", "password": "SecurePass1"},
    )
    assert login.status_code == 200
    assert login.json()["mfa_required"] is True
    assert login.json()["mfa_token"]

    verify = test_client.post(
        "/api/v1/auth/mfa/verify",
        json={"code": pyotp.TOTP(secret).now(), "mfa_token": login.json()["mfa_token"]},
    )
    assert verify.status_code == 200
    assert verify.json()["access_token"]


def test_partner_api_key_auth(client):
    test_client, _ = client
    created = test_client.post(
        "/api/v1/partners/keys",
        json={
            "name": "CERT Bridge",
            "partner_org": "National CERT",
            "scopes": ["institutions:read", "analytics:read"],
        },
    )
    assert created.status_code == 200
    raw_key = created.json()["api_key"]
    assert raw_key.startswith("msb_")

    me = test_client.get("/api/v1/partners/me", headers={"X-API-Key": raw_key})
    assert me.status_code == 200
    assert me.json()["partner_org"] == "National CERT"

    institutions = test_client.get("/api/v1/institutions", headers={"X-API-Key": raw_key})
    assert institutions.status_code == 200


def test_security_status_and_oidc_providers(client):
    test_client, _ = client
    status = test_client.get("/api/v1/auth/security-status").json()
    assert status["mfa_ready"] is True
    assert status["partner_api_keys_ready"] is True
    providers = test_client.get("/api/v1/auth/oidc/providers").json()
    assert "providers" in providers
