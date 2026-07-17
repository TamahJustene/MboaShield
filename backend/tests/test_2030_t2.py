"""MboaShield 2030 transformation phase T2 tests."""

from __future__ import annotations


def test_health_reports_t2(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "2.7.0"
    assert health["transformation_phase"] == "T7"


def test_trust_network_status(client):
    test_client, _ = client
    res = test_client.get("/api/v1/trust-network/status")
    assert res.status_code == 200
    body = res.json()
    assert "alert_types" in body
    assert "impersonation" in body["alert_types"]


def test_relationship_channel_and_alert_flow(client):
    test_client, _ = client
    rel = test_client.post(
        "/api/v1/trust-network/relationships",
        json={
            "source_institution_id": "minpostel",
            "target_institution_id": "antic",
            "status": "pending",
            "policy_note": "CERT pilot",
        },
    )
    assert rel.status_code == 200
    relationship = rel.json()
    assert relationship["id"]
    assert relationship["status"] == "pending"

    activated = test_client.patch(
        f"/api/v1/trust-network/relationships/{relationship['id']}",
        json={"status": "active"},
    )
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"

    channel = test_client.post(
        "/api/v1/trust-network/exchange/channels",
        json={
            "relationship_id": relationship["id"],
            "channel_type": "alert_share",
            "label": "Primary alert channel",
        },
    )
    assert channel.status_code == 200
    assert channel.json()["channel_type"] == "alert_share"

    alert = test_client.post(
        "/api/v1/trust-network/exchange/alerts",
        json={
            "alert_type": "impersonation",
            "title": "Fake MINPOSTEL handle",
            "summary": "@minpostel_fake active",
            "severity": "high",
            "source_institution_id": "minpostel",
            "target_institutions": ["antic"],
            "relationship_id": relationship["id"],
        },
    )
    assert alert.status_code == 200
    payload = alert.json()
    assert payload["alert_type"] == "impersonation"
    assert "antic" in payload["target_institutions"]

    inbox = test_client.get("/api/v1/trust-network/exchange/alerts?institution_id=antic")
    assert inbox.status_code == 200
    assert inbox.json()["count"] >= 1

    listed = test_client.get("/api/v1/trust-network/relationships?institution_id=minpostel")
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1
