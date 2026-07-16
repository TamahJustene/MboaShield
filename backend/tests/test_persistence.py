from __future__ import annotations

import importlib

from fastapi.testclient import TestClient


def test_text_checks_are_persisted(monkeypatch, tmp_path):
    db_path = tmp_path / "mboashield-test.db"
    monkeypatch.setenv("MBOASHIELD_DB_PATH", str(db_path))

    from backend.app import db as db_module
    from backend.app import main as main_module

    importlib.reload(db_module)
    reloaded_main = importlib.reload(main_module)
    client = TestClient(reloaded_main.app)

    response = client.post("/api/v1/check/text", json={"text": "URGENT send money now", "lang": "en"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["check_id"] >= 1
    assert db_path.exists()


def test_certificates_are_persisted(monkeypatch, tmp_path):
    db_path = tmp_path / "mboashield-test.db"
    monkeypatch.setenv("MBOASHIELD_DB_PATH", str(db_path))

    from backend.app import db as db_module
    from backend.app import main as main_module

    importlib.reload(db_module)
    reloaded_main = importlib.reload(main_module)
    client = TestClient(reloaded_main.app)

    lessons = client.get("/api/v1/ambassadors/lessons").json()["lessons"]
    lesson_id = lessons[0]["id"]
    response = client.post(
        "/api/v1/ambassadors/complete",
        json={"lesson_id": lesson_id, "learner_name": "Justene"},
    )

    assert response.status_code == 200
    assert db_path.exists()


def test_recent_checks_endpoint_returns_saved_history(monkeypatch, tmp_path):
    db_path = tmp_path / "mboashield-test.db"
    monkeypatch.setenv("MBOASHIELD_DB_PATH", str(db_path))

    from backend.app import db as db_module
    from backend.app import main as main_module

    importlib.reload(db_module)
    reloaded_main = importlib.reload(main_module)
    client = TestClient(reloaded_main.app)

    client.post("/api/v1/check/text", json={"text": "URGENT send money now", "lang": "en"})
    client.post(
        "/api/v1/check/impersonation",
        json={"name": "MINPOSTEL Officiel Verifie", "handle": "@minpostel_cm_info", "lang": "en"},
    )

    response = client.get("/api/v1/checks/recent?limit=2")
    payload = response.json()

    assert response.status_code == 200
    assert payload["count"] == 2
    assert payload["checks"][0]["check_type"] == "impersonation"
    assert payload["checks"][1]["check_type"] == "text"
    assert "result" in payload["checks"][0]


def test_recent_checks_endpoint_can_filter_by_type(monkeypatch, tmp_path):
    db_path = tmp_path / "mboashield-test.db"
    monkeypatch.setenv("MBOASHIELD_DB_PATH", str(db_path))

    from backend.app import db as db_module
    from backend.app import main as main_module

    importlib.reload(db_module)
    reloaded_main = importlib.reload(main_module)
    client = TestClient(reloaded_main.app)

    client.post("/api/v1/check/text", json={"text": "URGENT send money now", "lang": "en"})
    client.post(
        "/api/v1/check/impersonation",
        json={"name": "MINPOSTEL Officiel Verifie", "handle": "@minpostel_cm_info", "lang": "en"},
    )

    response = client.get("/api/v1/checks/recent?check_type=text")
    payload = response.json()

    assert response.status_code == 200
    assert payload["count"] == 1
    assert payload["checks"][0]["check_type"] == "text"


def test_get_check_by_id_returns_signals(monkeypatch, tmp_path):
    db_path = tmp_path / "mboashield-test.db"
    monkeypatch.setenv("MBOASHIELD_DB_PATH", str(db_path))

    from backend.app import db as db_module
    from backend.app import main as main_module

    importlib.reload(db_module)
    reloaded_main = importlib.reload(main_module)
    client = TestClient(reloaded_main.app)

    created = client.post("/api/v1/check/text", json={"text": "URGENT send money now", "lang": "en"}).json()
    check_id = created["check_id"]

    response = client.get(f"/api/v1/checks/{check_id}")
    payload = response.json()

    assert response.status_code == 200
    assert payload["id"] == check_id
    assert payload["check_type"] == "text"
    assert len(payload["signals"]) >= 1
    assert payload["signals"][0]["signal_type"] == "reason"


def test_get_check_by_id_returns_404_when_missing(monkeypatch, tmp_path):
    db_path = tmp_path / "mboashield-test.db"
    monkeypatch.setenv("MBOASHIELD_DB_PATH", str(db_path))

    from backend.app import db as db_module
    from backend.app import main as main_module

    importlib.reload(db_module)
    reloaded_main = importlib.reload(main_module)
    client = TestClient(reloaded_main.app)

    response = client.get("/api/v1/checks/999")
    assert response.status_code == 404


def test_certificate_lookup_endpoints(monkeypatch, tmp_path):
    db_path = tmp_path / "mboashield-test.db"
    monkeypatch.setenv("MBOASHIELD_DB_PATH", str(db_path))

    from backend.app import db as db_module
    from backend.app import main as main_module

    importlib.reload(db_module)
    reloaded_main = importlib.reload(main_module)
    client = TestClient(reloaded_main.app)

    lessons = client.get("/api/v1/ambassadors/lessons").json()["lessons"]
    completed = client.post(
        "/api/v1/ambassadors/complete",
        json={"lesson_id": lessons[0]["id"], "learner_name": "Justene"},
    ).json()
    certificate_id = completed["certificate"]["id"]

    one = client.get(f"/api/v1/certificates/{certificate_id}").json()
    recent = client.get("/api/v1/certificates/recent").json()

    assert one["certificate_id"] == certificate_id
    assert recent["count"] == 1
    assert recent["certificates"][0]["learner_name"] == "Justene"
