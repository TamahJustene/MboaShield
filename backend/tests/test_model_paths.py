from __future__ import annotations

import importlib

from fastapi.testclient import TestClient

from backend.app.services.model_adapters import analyze_audio_model, analyze_image_model
from backend.app.services.nlp_text import extract_features, score_text_nlp


def _client(monkeypatch, tmp_path):
    db_path = tmp_path / "mboashield-test.db"
    monkeypatch.setenv("MBOASHIELD_DB_PATH", str(db_path))

    from backend.app import db as db_module
    from backend.app import main as main_module
    from backend.app import seed as seed_module

    importlib.reload(db_module)
    importlib.reload(seed_module)
    return TestClient(importlib.reload(main_module).app)


def test_nlp_score_flags_scam_text():
    result = score_text_nlp("URGENT!!! Send money now via MoMo before account blocked")
    assert result["risk_score"] >= 50
    assert result["probability"] > 0.4
    assert result["top_features"]
    features = extract_features("URGENT send money MoMo")
    assert features["urgency"] > 0
    assert features["money"] > 0


def test_text_api_includes_nlp_block(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    response = client.post(
        "/api/v1/check/text",
        json={"text": "URGENT send money via MoMo now", "lang": "en"},
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["backend"] == "nlp+heuristic"
    assert "nlp" in payload
    assert payload["nlp"]["engine"].startswith("mboashield-text-nlp")


def test_media_adapter_scores_smooth_image():
    from PIL import Image
    import io

    img = Image.new("RGB", (64, 64), color=(180, 180, 180))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    result = analyze_image_model(buf.getvalue(), "synthetic_smooth_face.jpg")
    assert result["backend"] == "feature-model"
    assert result["risk_score"] >= 40
    assert "features" in result


def test_audio_adapter_scores_flat_wav():
    import io
    import wave
    import struct

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        frames = struct.pack("<" + "h" * 8000, *([100] * 8000))
        wf.writeframes(frames)
    result = analyze_audio_model(buf.getvalue(), "minister_voice_clone.wav")
    assert result["backend"] == "feature-model"
    assert result["risk_score"] >= 30


def test_health_lists_model_adapters(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    health = client.get("/health").json()
    assert health["version"] == "0.4.0"
    assert health["nlp_engine"] == "mboashield-text-nlp-v1"
    assert health["media_adapter"] == "mboashield-media-adapter-v1"
    assert health["audio_adapter"] == "mboashield-audio-adapter-v1"
