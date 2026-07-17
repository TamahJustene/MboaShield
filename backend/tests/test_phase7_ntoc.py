"""Phase 7 NTOC tests."""

from __future__ import annotations


def test_ntoc_dashboard_and_threat_level(client):
    test_client, _ = client
    threat = test_client.get("/api/v1/ntoc/threat-level")
    assert threat.status_code == 200
    body = threat.json()
    assert body["level"] in {"normal", "elevated", "high", "critical"}
    assert "score" in body

    dash = test_client.get("/api/v1/ntoc/dashboard")
    assert dash.status_code == 200
    payload = dash.json()
    assert payload["enabled"] is True
    assert "regional_map" in payload
    assert "institution_health" in payload


def test_case_lifecycle_notes_assign_evidence_and_notifications(client):
    test_client, _ = client
    registered = test_client.post(
        "/api/v1/auth/register",
        json={"display_name": "Case Analyst", "email": "case@mboashield.cm", "password": "SecurePass1"},
    ).json()
    headers = {"Authorization": f"Bearer {registered['access_token']}"}
    user_id = registered["user"]["id"]

    incident = test_client.post(
        "/api/v1/incidents",
        json={
            "report_type": "disinformation",
            "description": "Coordinated rumour campaign in Centre region",
            "region": "Centre",
            "priority": "high",
        },
    )
    assert incident.status_code == 200
    incident_id = incident.json()["id"]

    created = test_client.post(
        "/api/v1/cases",
        headers=headers,
        json={
            "title": "Centre rumour cluster",
            "summary": "Investigate coordinated messaging",
            "incident_id": incident_id,
            "region": "Centre",
            "priority": "high",
        },
    )
    assert created.status_code == 200
    case_id = created.json()["id"]

    note = test_client.post(
        f"/api/v1/cases/{case_id}/notes",
        headers=headers,
        json={"body": "Initial triage complete"},
    )
    assert note.status_code == 200

    assigned = test_client.post(
        f"/api/v1/cases/{case_id}/assign",
        headers=headers,
        json={"assignee_user_id": user_id, "note": "You own this"},
    )
    assert assigned.status_code == 200
    assert assigned.json()["assigned_to_user_id"] == user_id

    workspace = test_client.get(f"/api/v1/cases/{case_id}/workspace", headers=headers)
    assert workspace.status_code == 200
    assert workspace.json()["case"]["id"] == case_id
    assert len(workspace.json()["notes"]) >= 1

    evidence = test_client.get(f"/api/v1/cases/{case_id}/evidence", headers=headers)
    assert evidence.status_code == 200
    assert evidence.json()["case_id"] == case_id

    transition = test_client.post(
        f"/api/v1/incidents/{incident_id}/transition",
        headers=headers,
        json={"to_status": "analyst_review", "note": "Moving to analyst"},
    )
    assert transition.status_code == 200

    notes = test_client.get("/api/v1/notifications?audience=analyst", headers=headers)
    assert notes.status_code == 200
    assert notes.json()["count"] >= 1

    searched = test_client.get("/api/v1/cases?q=rumour", headers=headers)
    assert searched.status_code == 200
    assert searched.json()["count"] >= 1


def test_health_reports_phase7_version(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "1.9.0"
    assert health["ntoc"] is True
