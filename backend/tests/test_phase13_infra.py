"""Phase 13 enterprise infrastructure tests."""

from __future__ import annotations


def test_health_reports_phase13(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "2.4.0"
    assert health["metrics"] is True
    assert health["workers"] is False


def test_metrics_endpoint(client):
    test_client, _ = client
    test_client.get("/health")
    response = test_client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "mboashield_app_info" in body or "prometheus_client not installed" in body


def test_infra_status(client):
    test_client, _ = client
    response = test_client.get("/api/v1/infra/status")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "2.4.0"
    assert body["metrics_enabled"] is True
    assert body["workers_enabled"] is False
    assert body["workers_active"] is False


def test_sync_vault_retention_job(client):
    test_client, _ = client
    response = test_client.post("/api/v1/infra/jobs/vault-retention?dry_run=true")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["mode"] == "sync"
    assert "result" in body
    assert "purged" in body["result"] or "candidates" in body["result"] or "items" in body["result"]
