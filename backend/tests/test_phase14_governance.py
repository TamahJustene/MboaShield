"""Phase 14 governance tests."""

from __future__ import annotations


def test_governance_health_and_seed(client):
    test_client, _ = client
    health = test_client.get("/api/v1/governance/health")
    assert health.status_code == 200
    body = health.json()
    assert body["enabled"] is True
    assert body["certainty_policy"] == "none"
    assert body["risks"] >= 5
    assert body["model_cards"] >= 2
    assert body["dataset_cards"] >= 2


def test_consent_upsert_and_list(client):
    test_client, _ = client
    created = test_client.post(
        "/api/v1/governance/consent",
        json={"subject_key": "citizen-demo", "feature": "analytics_share", "granted": True},
    )
    assert created.status_code == 200, created.text
    assert created.json()["granted"] is True

    listed = test_client.get("/api/v1/governance/consent?subject_key=citizen-demo")
    assert listed.status_code == 200
    assert any(item["feature"] == "analytics_share" for item in listed.json()["items"])


def test_risk_register_linked_to_threat_model(client):
    test_client, _ = client
    risks = test_client.get("/api/v1/governance/risks")
    assert risks.status_code == 200
    items = risks.json()["items"]
    assert any(item["threat_model_ref"].startswith("TM-") for item in items)


def test_compliance_dashboard(client):
    test_client, _ = client
    response = test_client.get("/api/v1/governance/compliance")
    assert response.status_code == 200
    body = response.json()
    assert body["certainty_policy"] == "none"
    assert body["controls_implemented"] >= 1


def test_health_reports_phase14(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "2.8.0"
    assert health["governance"] is True
