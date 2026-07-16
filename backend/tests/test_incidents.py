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
    return TestClient(reloaded_main.app)


def test_create_and_list_incident_reports(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)

    check = client.post("/api/v1/check/text", json={"text": "URGENT send money now", "lang": "en"}).json()
    user = client.post("/api/v1/users", json={"display_name": "Reporter"}).json()

    created = client.post(
        "/api/v1/incidents",
        headers={"X-MboaShield-User-Id": str(user["id"])},
        json={
            "report_type": "scam",
            "description": "This WhatsApp message asked for MoMo transfer.",
            "verification_check_id": check["check_id"],
        },
    )
    payload = created.json()

    assert created.status_code == 200
    assert payload["status"] == "open"
    assert payload["report_type"] == "scam"
    assert payload["verification_check_id"] == check["check_id"]
    assert payload["user_id"] == user["id"]

    listed = client.get("/api/v1/incidents?status=open").json()
    assert listed["count"] == 1
    assert listed["reports"][0]["id"] == payload["id"]


def test_update_incident_status(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)

    created = client.post(
        "/api/v1/incidents",
        json={
            "report_type": "impersonation",
            "description": "Fake MINPOSTEL account circulating on WhatsApp.",
        },
    ).json()

    updated = client.patch(
        f"/api/v1/incidents/{created['id']}",
        json={"status": "reviewing", "reviewer_note": "Queued for analyst review"},
    )
    payload = updated.json()

    assert updated.status_code == 200
    assert payload["status"] == "reviewing"
    assert payload["reviewer_note"] == "Queued for analyst review"


def test_invalid_incident_type_rejected(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    response = client.post(
        "/api/v1/incidents",
        json={"report_type": "not_a_real_type", "description": "Something suspicious happened"},
    )
    assert response.status_code == 422
