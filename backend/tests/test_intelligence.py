from __future__ import annotations

from backend.app.services.engines import analyze_intelligence, list_engines
from backend.app.services.engines.trust_fusion import fuse
from backend.app.services.engines.text_intelligence import analyze as analyze_text


def test_engine_catalog_has_ten_modules():
    engines = list_engines()
    assert len(engines) == 10
    ids = {item["id"] for item in engines}
    assert "text_intelligence" in ids
    assert "video_intelligence" in ids
    assert "document_intelligence" in ids


def test_text_engine_flags_scam_pressure():
    result = analyze_text(text="URGENT send money now via MoMo", lang="en")
    assert result.status == "ok"
    assert result.risk_score >= 40
    assert result.confidence >= 1
    assert result.evidence
    assert result.reasoning
    assert result.recommendations


def test_intelligence_analyze_returns_trust_score(client):
    test_client, _ = client
    response = test_client.post(
        "/api/v1/intelligence/analyze",
        json={
            "text": "URGENT send money now via MoMo before account blocked",
            "name": "MINPOSTEL Officiel Verifie",
            "handle": "@minpostel_cm_info",
            "url": "https://bit.ly/fake-alert",
            "lang": "en",
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["trust_score"]["trust_score"] <= 100
    assert payload["trust_score"]["certainty"] == "none"
    assert payload["summary"]["active_engines"] >= 3
    assert len(payload["engines"]) == 10


def test_case_analyze_includes_engines_and_trust(client):
    test_client, _ = client
    response = test_client.post(
        "/api/v1/analyze",
        json={
            "text": "URGENT send money now",
            "name": "MINPOSTEL Officiel Verifie",
            "handle": "@minpostel_cm_info",
            "lang": "en",
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["modules"]
    assert payload["overall"]["engine_version"] == "0.7.0"
    assert "trust_score" in payload
    assert "engines" in payload
    assert payload["summary"]["explainable_trust_score"] == payload["trust_score"]["trust_score"]


def test_list_intelligence_engines(client):
    test_client, _ = client
    response = test_client.get("/api/v1/intelligence/engines")
    payload = response.json()
    assert response.status_code == 200
    assert payload["count"] == 10
    assert "confidence" in payload["contract"]


def test_fusion_never_claims_certainty():
    text_result = analyze_text(text="URGENT send money now", lang="en")
    fused = fuse([text_result], lang="en")
    assert fused["certainty"] == "none"
    assert "honesty_note" in fused
