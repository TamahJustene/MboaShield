from __future__ import annotations


def test_create_and_list_incident_reports(client):
    test_client, _ = client

    check = test_client.post("/api/v1/check/text", json={"text": "URGENT send money now", "lang": "en"}).json()
    user = test_client.post("/api/v1/users", json={"display_name": "Reporter"}).json()

    created = test_client.post(
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

    listed = test_client.get("/api/v1/incidents?status=open").json()
    assert listed["count"] == 1
    assert listed["reports"][0]["id"] == payload["id"]


def test_update_incident_status(client):
    test_client, _ = client

    created = test_client.post(
        "/api/v1/incidents",
        json={
            "report_type": "impersonation",
            "description": "Fake MINPOSTEL account circulating on WhatsApp.",
        },
    ).json()

    updated = test_client.patch(
        f"/api/v1/incidents/{created['id']}",
        json={"status": "reviewing", "reviewer_note": "Queued for analyst review"},
    )
    payload = updated.json()

    assert updated.status_code == 200
    assert payload["status"] == "reviewing"
    assert payload["reviewer_note"] == "Queued for analyst review"


def test_invalid_incident_type_rejected(client):
    test_client, _ = client
    response = test_client.post(
        "/api/v1/incidents",
        json={"report_type": "not_a_real_type", "description": "Something suspicious happened"},
    )
    assert response.status_code == 422
