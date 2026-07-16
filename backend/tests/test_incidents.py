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
    assert payload["status"] == "ai_analysis"
    assert payload["report_type"] == "scam"
    assert payload["verification_check_id"] == check["check_id"]
    assert payload["user_id"] == user["id"]
    assert payload["ai_summary"] is not None
    assert "analyst_review" in payload["next_actions"]

    listed = test_client.get("/api/v1/incidents?status=ai_analysis").json()
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
    assert created["status"] == "open"

    updated = test_client.patch(
        f"/api/v1/incidents/{created['id']}",
        json={"status": "reviewing", "reviewer_note": "Queued for analyst review"},
    )
    payload = updated.json()

    assert updated.status_code == 200
    assert payload["status"] == "reviewing"
    assert payload["reviewer_note"] == "Queued for analyst review"

    timeline = test_client.get(f"/api/v1/incidents/{created['id']}/timeline").json()
    assert timeline["count"] >= 2
    assert timeline["events"][-1]["to_status"] == "reviewing"


def test_invalid_incident_type_rejected(client):
    test_client, _ = client
    response = test_client.post(
        "/api/v1/incidents",
        json={"report_type": "not_a_real_type", "description": "Something suspicious happened"},
    )
    assert response.status_code == 422


def test_invalid_workflow_transition_rejected(client):
    test_client, _ = client
    created = test_client.post(
        "/api/v1/incidents",
        json={"report_type": "scam", "description": "Suspicious MoMo request on WhatsApp"},
    ).json()
    response = test_client.post(
        f"/api/v1/incidents/{created['id']}/transition",
        json={"to_status": "archived", "note": "Skip ahead illegally"},
    )
    assert response.status_code == 400


def test_national_workflow_happy_path(client):
    test_client, _ = client
    created = test_client.post(
        "/api/v1/incidents",
        json={"report_type": "disinformation", "description": "Rumour about fuel shortage spreading fast"},
    ).json()
    path = [
        "ai_analysis",
        "analyst_review",
        "institution_review",
        "decision",
        "public_advisory",
        "resolved",
        "archived",
    ]
    current = created
    for status in path:
        res = test_client.post(
            f"/api/v1/incidents/{current['id']}/transition",
            json={
                "to_status": status,
                "note": f"Move to {status}",
                "public_advisory": "Verify before sharing." if status == "public_advisory" else None,
                "decision_summary": "Confirmed disinformation risk" if status == "decision" else None,
            },
        )
        assert res.status_code == 200, res.text
        current = res.json()
        assert current["status"] == status
    assert current["status"] == "archived"


def test_analyst_queue_and_summary(client):
    test_client, _ = client
    test_client.post(
        "/api/v1/incidents",
        json={"report_type": "scam", "description": "Suspicious MoMo request on WhatsApp"},
    )
    queue = test_client.get("/api/v1/analyst/queue").json()
    summary = test_client.get("/api/v1/analyst/summary").json()
    assert queue["count"] >= 1
    assert summary["queue_total"] >= 1
    assert "open" in summary["workflow"]


def test_institution_admin_create_and_update(client):
    test_client, _ = client
    created = test_client.post(
        "/api/v1/institutions",
        json={
            "id": "demo_agency",
            "name": "Demo Cyber Agency",
            "short_name": "DCA",
            "url": "https://example.cm",
            "handles": ["@demo_agency"],
            "verified": True,
        },
    )
    assert created.status_code == 200
    assert created.json()["id"] == "demo_agency"

    updated = test_client.patch(
        "/api/v1/institutions/demo_agency",
        json={"handles": ["@demo_agency", "@dca_official"]},
    )
    assert updated.status_code == 200
    assert "@dca_official" in updated.json()["handles"]


def test_citizen_dashboard(client):
    test_client, _ = client
    user = test_client.post("/api/v1/users", json={"display_name": "Citizen Dash"}).json()
    test_client.post(
        "/api/v1/check/text",
        json={"text": "URGENT send money now", "lang": "en"},
        headers={"X-MboaShield-User-Id": str(user["id"])},
    )
    test_client.post(
        "/api/v1/incidents",
        headers={"X-MboaShield-User-Id": str(user["id"])},
        json={"report_type": "scam", "description": "Citizen saw a MoMo scam message"},
    )
    dash = test_client.get(
        "/api/v1/citizen/dashboard",
        headers={"X-MboaShield-User-Id": str(user["id"])},
    )
    assert dash.status_code == 200
    payload = dash.json()
    assert payload["checks_count"] >= 1
    assert payload["incidents_count"] >= 1
