from __future__ import annotations

import io
import struct
import wave

from PIL import Image

from backend.app.services.model_adapters import analyze_audio_model, analyze_image_model
from backend.app.services.nlp_text import extract_features, score_text_nlp


def test_nlp_score_flags_scam_text():
    result = score_text_nlp("URGENT!!! Send money now via MoMo before account blocked")
    assert result["risk_score"] >= 50
    assert result["probability"] > 0.4
    assert result["top_features"]
    features = extract_features("URGENT send money MoMo")
    assert features["urgency"] > 0


def test_text_api_includes_nlp_block(client):
    test_client, _ = client
    response = test_client.post("/api/v1/check/text", json={"text": "URGENT send money now", "lang": "en"})
    payload = response.json()
    assert response.status_code == 200
    assert "nlp" in payload or "ai_analysis" in payload


def test_image_feature_model_scores_suspicious_filename():
    buf = io.BytesIO()
    Image.new("RGB", (640, 360), color=(120, 40, 40)).save(buf, format="JPEG")
    result = analyze_image_model(buf.getvalue(), "deepfake_minister_ai_generated.jpg")
    assert result["backend"] == "feature-model"
    assert result["risk_score"] >= 30


def test_audio_feature_model_scores_clone_filename():
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(8000)
        frames = struct.pack("<" + "h" * 8000, *([100] * 8000))
        wf.writeframes(frames)
    result = analyze_audio_model(buf.getvalue(), "minister_voice_clone.wav")
    assert result["backend"] == "feature-model"
    assert result["risk_score"] >= 30


def test_health_lists_model_adapters(client):
    test_client, _ = client
    response = test_client.get("/health")
    payload = response.json()
    assert response.status_code == 200
    assert payload["nlp_engine"] == "mboashield-text-nlp-v1"
    assert payload["media_adapter"] == "mboashield-media-adapter-v1"
    assert payload["audio_adapter"] == "mboashield-audio-adapter-v1"
