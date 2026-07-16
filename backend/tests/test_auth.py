from __future__ import annotations


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
