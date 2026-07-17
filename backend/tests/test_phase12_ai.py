"""Phase 12 advanced AI platform tests."""

from __future__ import annotations


def test_model_registry_and_evaluation_en(client):
    test_client, _ = client
    health = test_client.get("/api/v1/ai-platform/health")
    assert health.status_code == 200
    body = health.json()
    assert body["engine_package_version"] == "1.2.0"
    assert body["models"] >= 3

    models = test_client.get("/api/v1/ai-platform/models")
    assert models.status_code == 200
    assert models.json()["count"] >= 3

    checksum = test_client.get("/api/v1/ai-platform/models/mboashield-text-nlp-v1/verify-checksum")
    assert checksum.status_code == 200
    assert checksum.json()["valid"] is True

    run = test_client.post("/api/v1/ai-platform/evaluation/run", json={"dataset": "en"})
    assert run.status_code == 200, run.text
    metrics = run.json()["metrics"]
    assert metrics["cases"] >= 3
    assert metrics["pass_rate"] >= 0.5
    assert metrics["certainty"] == "none"

    latest = test_client.get("/api/v1/ai-platform/evaluation/latest?dataset=en")
    assert latest.status_code == 200


def test_intelligence_includes_calibrated_score_field(client):
    test_client, _ = client
    response = test_client.post(
        "/api/v1/intelligence/analyze",
        json={"text": "URGENT send MoMo now", "lang": "en"},
    )
    assert response.status_code == 200
    trust = response.json()["trust_score"]
    assert trust["certainty"] == "none"
    assert "calibrated_score" in trust
    assert response.json()["advanced_ai"]["enabled"] is True


def test_health_reports_phase12_version(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "2.7.0"
    assert health["advanced_ai"] is True
