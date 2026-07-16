from __future__ import annotations


def test_text_checks_are_persisted(client):
    test_client, db_path = client
    response = test_client.post("/api/v1/check/text", json={"text": "URGENT send money now", "lang": "en"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["check_id"] >= 1
    assert db_path.exists()


def test_certificates_are_persisted(client):
    test_client, db_path = client
    lessons = test_client.get("/api/v1/ambassadors/lessons").json()["lessons"]
    lesson_id = lessons[0]["id"]
    response = test_client.post(
        "/api/v1/ambassadors/complete",
        json={"lesson_id": lesson_id, "learner_name": "Justene"},
    )

    assert response.status_code == 200
    assert db_path.exists()


def test_recent_checks_endpoint_returns_saved_history(client):
    test_client, _ = client
    test_client.post("/api/v1/check/text", json={"text": "URGENT send money now", "lang": "en"})
    test_client.post(
        "/api/v1/check/impersonation",
        json={"name": "MINPOSTEL Officiel Verifie", "handle": "@minpostel_cm_info", "lang": "en"},
    )

    response = test_client.get("/api/v1/checks/recent?limit=2")
    payload = response.json()

    assert response.status_code == 200
    assert payload["count"] == 2
    assert payload["checks"][0]["check_type"] == "impersonation"
    assert payload["checks"][1]["check_type"] == "text"
    assert "result" in payload["checks"][0]


def test_recent_checks_endpoint_can_filter_by_type(client):
    test_client, _ = client
    test_client.post("/api/v1/check/text", json={"text": "URGENT send money now", "lang": "en"})
    test_client.post(
        "/api/v1/check/impersonation",
        json={"name": "MINPOSTEL Officiel Verifie", "handle": "@minpostel_cm_info", "lang": "en"},
    )

    response = test_client.get("/api/v1/checks/recent?check_type=text")
    payload = response.json()

    assert response.status_code == 200
    assert payload["count"] == 1
    assert payload["checks"][0]["check_type"] == "text"


def test_get_check_by_id_returns_signals(client):
    test_client, _ = client
    created = test_client.post("/api/v1/check/text", json={"text": "URGENT send money now", "lang": "en"}).json()
    check_id = created["check_id"]

    response = test_client.get(f"/api/v1/checks/{check_id}")
    payload = response.json()

    assert response.status_code == 200
    assert payload["id"] == check_id
    assert payload["check_type"] == "text"
    assert len(payload["signals"]) >= 1
    assert payload["signals"][0]["signal_type"] == "reason"


def test_get_check_by_id_returns_404_when_missing(client):
    test_client, _ = client
    response = test_client.get("/api/v1/checks/999")
    assert response.status_code == 404


def test_certificate_lookup_endpoints(client):
    test_client, _ = client
    lessons = test_client.get("/api/v1/ambassadors/lessons").json()["lessons"]
    completed = test_client.post(
        "/api/v1/ambassadors/complete",
        json={"lesson_id": lessons[0]["id"], "learner_name": "Justene"},
    ).json()
    certificate_id = completed["certificate"]["id"]

    one = test_client.get(f"/api/v1/certificates/{certificate_id}").json()
    recent = test_client.get("/api/v1/certificates/recent").json()

    assert one["certificate_id"] == certificate_id
    assert recent["count"] == 1
    assert recent["certificates"][0]["learner_name"] == "Justene"
