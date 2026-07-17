"""MboaShield 2030 transformation phase T6 tests."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_health_reports_t6(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "2.8.0"
    assert health["transformation_phase"] == "CI-1"


def test_infra_resilience_endpoint(client):
    test_client, _ = client
    res = test_client.get("/api/v1/infra/resilience")
    assert res.status_code == 200
    body = res.json()
    assert body["targets"]["rpo_minutes"] == 15
    assert body["targets"]["rto_hours"] == 4
    assert "locustfile.py" in body["load_tests"]["locust"]
    assert "trust_assess.js" in body["load_tests"]["k6"]


def test_load_and_dr_artifacts_exist():
    assert (ROOT / "scripts" / "load" / "locustfile.py").is_file()
    assert (ROOT / "scripts" / "load" / "trust_assess.js").is_file()
    assert (ROOT / "docs" / "HA_AND_SCALE.md").is_file()
    assert (ROOT / "docs" / "DR_RUNBOOK.md").is_file()
    assert (ROOT / "docs" / "adr" / "0007-resilience-and-scale-proof.md").is_file()
    locust = (ROOT / "scripts" / "load" / "locustfile.py").read_text(encoding="utf-8")
    assert "trust/assess" in locust
    k6 = (ROOT / "scripts" / "load" / "trust_assess.js").read_text(encoding="utf-8")
    assert "trust/assess" in k6
