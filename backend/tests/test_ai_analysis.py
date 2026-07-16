from __future__ import annotations

from backend.app.services.ai_analysis import enrich_result


def test_enrich_result_adds_ai_analysis_block():
    raw = {
        "risk_score": 82,
        "risk_band": "high",
        "reasons": ["Matched high-risk pattern: /urgent/", "Long claim without any source link"],
        "advice": "Do not forward.",
        "source_verification": {"status": "likely_scam", "scam_signals": ["urgent"], "matched_sources": [], "summary": "scam"},
    }
    enriched = enrich_result(raw, modality="text", lang="en")
    assert "ai_analysis" in enriched
    assert enriched["ai_analysis"]["confidence"] >= 1
    assert enriched["ai_analysis"]["threat_categories"]
    assert enriched["ai_analysis"]["evidence"]
    assert enriched["ai_analysis"]["narrative"]


def test_text_check_returns_ai_analysis(client):
    test_client, _ = client
    response = test_client.post("/api/v1/check/text", json={"text": "URGENT send money now", "lang": "en"})
    payload = response.json()
    assert response.status_code == 200
    assert "ai_analysis" in payload
    assert payload["ai_analysis"]["engine"] == "mboashield-trust-engine"


def test_case_analyze_endpoint_combines_modules(client):
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
    assert len(payload["modules"]) >= 2
    assert payload["case_check_id"] >= 1


def test_health_exposes_ai_engine(client):
    test_client, _ = client
    response = test_client.get("/health")
    payload = response.json()
    assert response.status_code == 200
    assert payload["ai_engine"] == "mboashield-trust-engine"
    assert payload["ai_engine_version"] == "0.6.0"
