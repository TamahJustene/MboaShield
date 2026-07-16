from __future__ import annotations


def test_institutions_are_seeded_and_listed(client):
    test_client, db_path = client

    response = test_client.get("/api/v1/institutions")
    payload = response.json()

    assert response.status_code == 200
    assert db_path.exists()
    assert payload["count"] == 17
    assert payload["institutions"][0]["short_name"]
    assert "handles" in payload["institutions"][0]


def test_get_institution_by_id(client):
    test_client, _ = client

    response = test_client.get("/api/v1/institutions/minpostel")
    payload = response.json()

    assert response.status_code == 200
    assert payload["id"] == "minpostel"
    assert payload["short_name"] == "MINPOSTEL"


def test_create_and_fetch_user(client):
    test_client, _ = client

    created = test_client.post(
        "/api/v1/users",
        json={"display_name": "Justene Nkwagoh Tamah", "email": "tamahjustene45@gmail.com"},
    ).json()
    fetched = test_client.get(f"/api/v1/users/{created['id']}").json()

    assert created["display_name"] == "Justene Nkwagoh Tamah"
    assert created["role"] == "citizen"
    assert fetched["email"] == "tamahjustene45@gmail.com"


def test_checks_can_be_linked_to_user(client):
    test_client, _ = client

    user = test_client.post("/api/v1/users", json={"display_name": "Citizen One"}).json()
    response = test_client.post(
        "/api/v1/check/text",
        json={"text": "URGENT send money now", "lang": "en"},
        headers={"X-MboaShield-User-Id": str(user["id"])},
    )

    assert response.status_code == 200
    assert response.json()["check_id"] >= 1


def test_health_reports_phase1_foundation(client):
    test_client, _ = client
    response = test_client.get("/health")
    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["database"] == "sqlite"
    assert payload["auth_enforce"] is False
    assert payload["version"] == "1.1.0"
