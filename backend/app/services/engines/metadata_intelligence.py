from __future__ import annotations

from .base import EngineResult, clamp, risk_band, skipped

RISKY_NAME_TOKENS = [
    "deepfake",
    "ai_generated",
    "synthetic",
    "clone",
    "voice_clone",
    "fake",
    "generated",
]


def analyze(*, filename: str = "", mime_type: str = "", size_bytes: int | None = None) -> EngineResult:
    if not filename and not mime_type and size_bytes is None:
        return skipped("metadata_intelligence", "Metadata Intelligence", "No file metadata provided.")

    evidence = []
    score = 10
    lowered = (filename or "").lower()
    for token in RISKY_NAME_TOKENS:
        if token in lowered:
            score += 18
            evidence.append({"label": f"Filename token: {token}", "weight": 15, "kind": "metadata_signal"})

    if mime_type:
        evidence.append({"label": f"MIME type: {mime_type}", "weight": 8, "kind": "metadata_signal"})
    if size_bytes is not None:
        evidence.append({"label": f"Payload size: {size_bytes} bytes", "weight": 6, "kind": "metadata_signal"})
        if size_bytes < 2048:
            score += 8
            evidence.append({"label": "Very small media payload", "weight": 9, "kind": "metadata_risk"})

    score = clamp(score)
    threats = ["synthetic_media"] if score >= 40 else []
    return EngineResult(
        engine_id="metadata_intelligence",
        engine_name="Metadata Intelligence",
        confidence=clamp(38 + len(evidence) * 6),
        evidence=evidence or [{"label": "Basic metadata inspected", "weight": 5, "kind": "metadata_signal"}],
        reasoning="Filename, MIME, and size cues were inspected for synthetic-media naming patterns.",
        risk_level=risk_band(score),
        risk_score=score,
        threat_category=threats,
        recommendations=["Do not rely on filename claims; validate content through trusted channels."],
        details={"filename": filename, "mime_type": mime_type, "size_bytes": size_bytes},
    )
