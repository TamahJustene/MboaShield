from __future__ import annotations

from ..model_adapters import analyze_image_with_fallback
from .base import EngineResult, clamp, risk_band, skipped


def analyze(*, data: bytes | None = None, filename: str = "", lang: str = "en") -> EngineResult:
    if not data:
        return skipped("image_intelligence", "Image Intelligence", "No image bytes provided.")

    raw = analyze_image_with_fallback(data, filename or "", lang)
    score = clamp(raw.get("risk_score", 0) or 0)
    evidence = [{"label": reason, "weight": 12, "kind": "image_signal"} for reason in raw.get("reasons", [])[:6]]
    for feature in (raw.get("top_features") or [])[:3]:
        evidence.append(
            {
                "label": f"Feature: {feature.get('name')} ({feature.get('value')})",
                "weight": 10,
                "kind": "feature_signal",
            }
        )

    return EngineResult(
        engine_id="image_intelligence",
        engine_name="Image Intelligence",
        confidence=clamp(40 + min(25, len(evidence) * 5) + score * 0.12),
        evidence=evidence,
        reasoning=raw.get("advice")
        or "Image risk scored via feature-model adapter with heuristic fallback.",
        risk_level=risk_band(score),
        risk_score=score,
        threat_category=["synthetic_media"] if score >= 40 else [],
        recommendations=[
            "Treat sensational images as unverified until confirmed by official channels.",
            "Prefer original capture context over forwarded screenshots.",
        ],
        details={"backend": raw.get("backend"), "filename": filename},
    )
