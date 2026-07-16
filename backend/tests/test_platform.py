from __future__ import annotations

import importlib

from fastapi.testclient import TestClient


def _client(monkeypatch, tmp_path):
    db_path = tmp_path / "mboashield-test.db"
    monkeypatch.setenv("MBOASHIELD_DB_PATH", str(db_path))

    from backend.app import db as db_module
    from backend.app import main as main_module
    from backend.app import seed as seed_module

    importlib.reload(db_module)
    importlib.reload(seed_module)
    reloaded_main = importlib.reload(main_module)
    return TestClient(reloaded_main.app), db_path


def test_institutions_are_seeded_and_listed(monkeypatch, tmp_path):
    client, db_path = _client(monkeypatch, tmp_path)

    response = client.get("/api/v1/institutions")
    payload = response.json()

    assert response.status_code == 200
    assert db_path.exists()
    assert payload["count"] == 17
    assert payload["institutions"][0]["short_name"]
    assert "handles" in payload["institutions"][0]


def test_get_institution_by_id(monkeypatch, tmp_path):
    client, _ = _client(monkeypatch, tmp_path)

    response = client.get("/api/v1/institutions/minpostel")
    payload = response.json()

    assert response.status_code == 200
    assert payload["id"] == "minpostel"
    assert payload["short_name"] == "MINPOSTEL"


def test_create_and_fetch_user(monkeypatch, tmp_path):
    client, _ = _client(monkeypatch, tmp_path)

    created = client.post(
        "/api/v1/users",
        json={"display_name": "Justene Nkwagoh Tamah", "email": "tamahjustene45@gmail.com"},
    ).json()
    fetched = client.get(f"/api/v1/users/{created['id']}").json()

    assert created["display_name"] == "Justene Nkwagoh Tamah"
    assert created["role"] == "citizen"
    assert fetched["email"] == "tamahjustene45@gmail.com"


def test_checks_can_be_linked_to_user(monkeypatch, tmp_path):
    client, _ = _client(monkeypatch, tmp_path)

    user = client.post("/api/v1/users", json={"display_name": "Citizen One"}).json()
    response = client.post(
        "/api/v1/check/text",
        json={"text": "URGENT send money now", "lang": "en"},
        headers={"X-MboaShield-User-Id": str(user["id"])},
    )

    assert response.status_code == 200
    assert response.json()["check_id"] >= 1
