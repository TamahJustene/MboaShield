from __future__ import annotations


def test_national_analytics_endpoint(client):
    test_client, _ = client
    test_client.post("/api/v1/check/text", json={"text": "URGENT send money now", "lang": "en"})
    test_client.post(
        "/api/v1/incidents",
        json={
            "report_type": "scam",
            "description": "Regional scam report for analytics",
            "region": "Littoral",
        },
    )
    response = test_client.get("/api/v1/analytics/national")
    payload = response.json()
    assert response.status_code == 200
    assert payload["overview"]["checks_total"] >= 1
    assert payload["overview"]["incidents_total"] >= 1
    assert "threat_trends" in payload
    assert "regional_heat_map" in payload
    assert "ai_accuracy" in payload
    assert payload["ai_accuracy"]["honesty_note"]
    littoral = next(item for item in payload["regional_heat_map"] if item["region"] == "Littoral")
    assert littoral["incident_count"] >= 1


def test_analytics_slice_endpoints(client):
    test_client, _ = client
    for path in [
        "/api/v1/analytics/threats",
        "/api/v1/analytics/regions",
        "/api/v1/analytics/incidents/timeline",
        "/api/v1/analytics/performance",
        "/api/v1/analytics/participation",
    ]:
        res = test_client.get(path)
        assert res.status_code == 200, path


def test_analysis_feedback_updates_accuracy(client):
    test_client, _ = client
    check = test_client.post("/api/v1/check/text", json={"text": "URGENT send money now", "lang": "en"}).json()
    feedback = test_client.post(
        "/api/v1/analytics/feedback",
        json={
            "verification_check_id": check["check_id"],
            "label": "true_positive",
            "note": "Confirmed scam pattern",
        },
    )
    assert feedback.status_code == 200
    perf = test_client.get("/api/v1/analytics/performance").json()
    assert perf["ai_accuracy"]["labeled_feedback"]["true_positive"] >= 1
    assert perf["ai_accuracy"]["accuracy"] == 1.0


def test_response_time_after_resolution(client):
    test_client, _ = client
    created = test_client.post(
        "/api/v1/incidents",
        json={"report_type": "disinformation", "description": "Need response timing sample"},
    ).json()
    for status in ["ai_analysis", "analyst_review", "decision", "resolved"]:
        res = test_client.post(
            f"/api/v1/incidents/{created['id']}/transition",
            json={"to_status": status, "note": f"to {status}"},
        )
        assert res.status_code == 200
    timeline = test_client.get("/api/v1/analytics/incidents/timeline").json()
    assert timeline["response_time"]["sample_size"] >= 1
