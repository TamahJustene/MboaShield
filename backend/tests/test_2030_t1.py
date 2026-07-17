"""MboaShield 2030 transformation phase T1 tests."""

from __future__ import annotations


def test_health_reports_t1(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "2.7.0"
    assert health["transformation_phase"] == "T7"


def test_program_endpoint_t1(client):
    test_client, _ = client
    body = test_client.get("/api/v1/program").json()
    assert body["transformation_phase"] == "T7"
    assert body["version"] == "2.7.0"


def test_trust_assess_text(client):
    test_client, _ = client
    res = test_client.post(
        "/api/v1/trust/assess",
        json={
            "object_type": "text",
            "text": "URGENT: send mobile money now to verify your account",
            "lang": "en",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["object_type"] == "text"
    assert 0 <= data["score"] <= 100
    assert data["band"] in {"low", "medium", "high"}
    assert data["certainty"] == "none"
    assert data["id"] is not None
    assert data["verification_check_id"] is not None
    assert data["check_id"] == data["verification_check_id"]
    assert data["risk_score"] is not None
    assert isinstance(data["signals"], list)

    fetched = test_client.get(f"/api/v1/trust/assessments/{data['id']}").json()
    assert fetched["id"] == data["id"]
    assert fetched["score"] == data["score"]


def test_trust_assess_verification_check_bridge(client):
    test_client, _ = client
    check = test_client.post(
        "/api/v1/check/text",
        json={"text": "Official MINPOSTEL grant - click here", "lang": "en"},
    ).json()
    bridged = test_client.post(
        "/api/v1/trust/assess",
        json={
            "object_type": "verification_check",
            "verification_check_id": check["check_id"],
        },
    ).json()
    assert bridged["object_type"] == "verification_check"
    assert bridged["verification_check_id"] == check["check_id"]
    assert bridged["score"] is not None


def test_trust_assess_intelligence(client):
    test_client, _ = client
    res = test_client.post(
        "/api/v1/trust/assess",
        json={
            "object_type": "intelligence",
            "text": "Free Bitcoin giveaway from the president",
            "name": "MINFIN",
            "handle": "@minfin_official_fake",
            "lang": "en",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["object_type"] == "intelligence"
    assert data["trust_score"] is not None
