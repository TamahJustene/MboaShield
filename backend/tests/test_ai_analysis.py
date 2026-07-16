from __future__ import annotations

import importlib

from fastapi.testclient import TestClient

from backend.app.services.ai_analysis import enrich_result


def _client(monkeypatch, tmp_path):
    db_path = tmp_path / "mboashield-test.db"
    monkeypatch.setenv("MBOASHIELD_DB_PATH", str(db_path))

    from backend.app import db as db_module
    from backend.app import main as main_module
    from backend.app import seed as seed_module

    importlib.reload(db_module)
    importlib.reload(seed_module)
    return TestClient(importlib.reload(main_module).app)


def test_enrich_result_adds_ai_analysis_block():
    raw = {
        "risk_score": 82,
        "risk_band": "high",
        "reasons": ["Matched high-risk pattern: /urgent/", "Long claim without any source link"],
        "advice": "Do not forward.",
        "source_verification": {"status": "likely_scam", "scam_signals": ["urgent"], "matched_sources": [], "summary": "scam"},
    }
    enriched = enrich_result(raw, modality="text", lang="en")
    ai = enriched["ai_analysis"]

    assert ai["engine"] == "mboashield-trust-engine"
    assert ai["confidence"] >= 50
    assert "scam" in ai["threat_categories"] or "disinformation" in ai["threat_categories"]
    assert ai["narrative"]
    assert ai["next_actions"]


def test_text_check_returns_ai_analysis(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    response = client.post("/api/v1/check/text", json={"text": "URGENT send money now via MoMo", "lang": "en"})
    payload = response.json()

    assert response.status_code == 200
    assert "ai_analysis" in payload
    assert payload["ai_analysis"]["modality"] == "text"
    assert payload["ai_analysis"]["confidence"] >= 1


def test_case_analyze_endpoint_combines_modules(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    response = client.post(
        "/api/v1/analyze",
        json={
            "text": "URGENT!!! Le ministre annonce un couvre-feu. Envoie de l'argent au MoMo.",
            "name": "MINPOSTEL Officiel Verifie",
            "handle": "@minpostel_cm_info",
            "lang": "en",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["overall"]["modality"] == "case"
    assert payload["summary"]["module_count"] == 2
    assert payload["case_check_id"] >= 1
    assert len(payload["modules"]) == 2


def test_health_exposes_ai_engine(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    health = client.get("/health").json()
    assert health["version"] == "0.4.0"
    assert health["ai_engine"] == "mboashield-trust-engine"
