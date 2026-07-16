"""Model-ready adapters for media and audio.

Each adapter:
1. extracts a feature vector
2. applies calibrated model weights
3. falls back to the existing heuristic path on failure

This keeps production stable while leaving a clean replacement point for ONNX /
deepfake models later.
"""

from __future__ import annotations

import io
import json
import math
import struct
import wave
from functools import lru_cache
from typing import Any

from PIL import Image, ImageStat

from ..config import DATA_DIR


def _band(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


@lru_cache(maxsize=1)
def _media_weights() -> dict[str, Any]:
    return json.loads((DATA_DIR / "media_weights.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _audio_weights() -> dict[str, Any]:
    return json.loads((DATA_DIR / "audio_weights.json").read_text(encoding="utf-8"))


def _score_features(features: dict[str, float], cfg: dict[str, Any]) -> tuple[int, float, list[dict[str, float | str]]]:
    bias = float(cfg.get("bias", 0.0))
    weights: dict[str, float] = cfg.get("weights", {})
    linear = bias
    top: list[dict[str, float | str]] = []
    for key, weight in weights.items():
        value = float(features.get(key, 0.0))
        contrib = weight * value
        linear += contrib
        if value > 0:
            top.append({"name": key, "value": round(value, 4), "contribution": round(contrib, 4)})
    top.sort(key=lambda item: float(item["contribution"]), reverse=True)
    probability = _sigmoid(linear * 3.0)
    score = int(round(probability * 100))
    return max(0, min(100, score)), probability, top[:5]


def analyze_image_model(data: bytes, filename: str = "") -> dict[str, Any]:
    """Feature-model path for images. Raises on hard decode failure."""
    cfg = _media_weights()
    img = Image.open(io.BytesIO(data)).convert("RGB")
    w, h = img.size
    ratio = w / max(h, 1)
    exif = img.getexif()
    stat = ImageStat.Stat(img)
    mean_var = sum(stat.var) / max(len(stat.var), 1)
    lowered = (filename or "").lower()

    features = {
        "small_resolution": 1.0 if w * h < 80_000 else 0.0,
        "odd_aspect": 1.0 if ratio < 0.45 or ratio > 2.3 else 0.0,
        "no_exif": 1.0 if not exif or len(exif) == 0 else 0.0,
        "smooth_variance": 1.0 if mean_var < 1200 else 0.0,
        "noisy_variance": 1.0 if mean_var > 9000 else 0.0,
        "filename_synthetic": 1.0
        if any(token in lowered for token in ["synthetic", "ai", "deepfake", "generated", "face"])
        else 0.0,
        "byte_density": min(1.0, len(data) / max(w * h, 1) / 3.0),
    }
    score, probability, top = _score_features(features, cfg)
    reasons = [
        f"Media model feature '{item['name']}' activated ({item['value']})"
        for item in top
    ]
    if not reasons:
        reasons.append("Media model found weak synthetic-media features")

    return {
        "engine": cfg.get("name", "mboashield-media-adapter-v1"),
        "engine_version": cfg.get("version", "1.0.0"),
        "backend": "feature-model",
        "risk_score": score,
        "risk_band": _band(score),
        "probability": round(probability, 4),
        "reasons": reasons,
        "features": features,
        "top_features": top,
        "meta": {
            "filename": filename,
            "bytes": len(data),
            "width": w,
            "height": h,
            "mean_variance": round(mean_var, 2),
            "exif_tags": len(exif) if exif else 0,
        },
    }


def analyze_audio_model(data: bytes, filename: str = "") -> dict[str, Any]:
    """Feature-model path for audio. Raises when WAV decode is impossible and no features exist."""
    cfg = _audio_weights()
    lowered = (filename or "").lower()
    features = {
        "tiny_file": 1.0 if len(data) < 8_000 else 0.0,
        "filename_clone": 1.0
        if any(token in lowered for token in ["voice", "clone", "ministre", "minister", "urgent", "officiel"])
        else 0.0,
        "short_duration": 0.0,
        "flat_dynamics": 0.0,
        "low_dynamics": 0.0,
        "high_sample_rate": 0.0,
        "unknown_format": 0.0,
    }
    meta: dict[str, Any] = {"filename": filename, "bytes": len(data)}

    try:
        with wave.open(io.BytesIO(data), "rb") as wf:
            channels = wf.getnchannels()
            rate = wf.getframerate()
            n_frames = wf.getnframes()
            sampwidth = wf.getsampwidth()
            raw = wf.readframes(min(n_frames, rate * 30))
            duration = n_frames / max(rate, 1)
            meta.update(
                {
                    "sample_rate": rate,
                    "channels": channels,
                    "duration_sec": round(duration, 2),
                    "format": "wav",
                }
            )
            features["short_duration"] = 1.0 if duration < 3 else 0.0
            features["high_sample_rate"] = 1.0 if rate > 48_000 else 0.0

            if sampwidth == 2:
                count = len(raw) // 2
                samples = struct.unpack(f"<{count}h", raw[: count * 2])
            elif sampwidth == 1:
                samples = [b - 128 for b in raw]
            else:
                samples = []

            if samples:
                peak = max(abs(s) for s in samples) or 1
                amps = [abs(s) / peak for s in samples[:: max(1, len(samples) // 500)]]
                mean_amp = sum(amps) / len(amps)
                variance = sum((a - mean_amp) ** 2 for a in amps) / len(amps)
                meta["amplitude_variance"] = round(variance, 6)
                features["flat_dynamics"] = 1.0 if variance < 0.002 else 0.0
                features["low_dynamics"] = 1.0 if 0.002 <= variance < 0.008 else 0.0
    except Exception:
        features["unknown_format"] = 1.0
        meta["format"] = "unknown_or_compressed"

    score, probability, top = _score_features(features, cfg)
    reasons = [
        f"Audio model feature '{item['name']}' activated ({item['value']})"
        for item in top
    ]
    if not reasons:
        reasons.append("Audio model found weak voice-clone features")

    return {
        "engine": cfg.get("name", "mboashield-audio-adapter-v1"),
        "engine_version": cfg.get("version", "1.0.0"),
        "backend": "feature-model",
        "risk_score": score,
        "risk_band": _band(score),
        "probability": round(probability, 4),
        "reasons": reasons,
        "features": features,
        "top_features": top,
        "meta": meta,
    }


def analyze_image_with_fallback(data: bytes, filename: str = "", lang: str = "en") -> dict[str, Any]:
    from . import media_check

    try:
        model = analyze_image_model(data, filename)
        advice = {
            "high": "Strong synthetic signals. Do not treat this image as proof.",
            "medium": "Mixed signals. Ask for the original source (raw photo).",
            "low": "Few model flags. Still verify context before trusting it.",
        }
        if lang.startswith("fr"):
            advice = {
                "high": "Signaux synthetiques eleves. Ne traitez pas cette image comme une preuve.",
                "medium": "Signaux mixtes. Demandez la source originale (photo brute).",
                "low": "Peu de signaux modeles. Verifiez quand meme le contexte.",
            }
        return {
            "risk_score": model["risk_score"],
            "risk_band": model["risk_band"],
            "reasons": model["reasons"][:8],
            "meta": {**model["meta"], "model": model},
            "advice": advice[model["risk_band"]],
            "engine": model["engine"],
            "engine_version": model["engine_version"],
            "backend": model["backend"],
            "model_probability": model["probability"],
        }
    except Exception as exc:  # noqa: BLE001
        fallback = media_check.check_image_bytes(data, filename, lang).as_dict()
        fallback["backend"] = "heuristic-fallback"
        fallback["fallback_reason"] = str(exc)
        return fallback


def analyze_audio_with_fallback(data: bytes, filename: str = "", lang: str = "en") -> dict[str, Any]:
    from . import audio_check

    try:
        model = analyze_audio_model(data, filename)
        advice = {
            "high": "High voice-clone risk. Do not send money. Verify via official website.",
            "medium": "Mixed signals. Demand written confirmation on an official channel.",
            "low": "Few suspicious audio signals. Stay cautious before acting.",
        }
        if lang.startswith("fr"):
            advice = {
                "high": "Risque eleve de voix clonee. Ne transferez pas d'argent. Verifiez via le site officiel.",
                "medium": "Signaux mixtes. Demandez confirmation ecrite sur un canal officiel.",
                "low": "Peu de signaux audio suspects. Restez vigilant avant toute action.",
            }
        return {
            "risk_score": model["risk_score"],
            "risk_band": model["risk_band"],
            "reasons": model["reasons"][:8],
            "meta": {**model["meta"], "model": model},
            "advice": advice[model["risk_band"]],
            "engine": model["engine"],
            "engine_version": model["engine_version"],
            "backend": model["backend"],
            "model_probability": model["probability"],
        }
    except Exception as exc:  # noqa: BLE001
        fallback = audio_check.check_audio_bytes(data, filename, lang).as_dict()
        fallback["backend"] = "heuristic-fallback"
        fallback["fallback_reason"] = str(exc)
        return fallback
