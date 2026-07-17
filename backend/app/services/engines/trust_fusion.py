"""Fuse engine outputs into one Explainable Trust Score.

Trust is the inverse of fused risk. Higher trust means lower assessed threat risk.
Never claims certainty.
"""

from __future__ import annotations

from typing import Any

from .base import EngineResult, clamp, risk_band


def fuse(engine_results: list[EngineResult], *, lang: str = "en", calibration: dict[str, Any] | None = None) -> dict[str, Any]:
    active = [item for item in engine_results if item.status == "ok"]
    if not active:
        return {
            "trust_score": 50,
            "trust_band": "medium",
            "fused_risk_score": 50,
            "fused_risk_level": "medium",
            "confidence": 20,
            "threat_categories": [],
            "evidence": [],
            "reasoning": "No active intelligence engines contributed signals.",
            "recommendations": ["Provide text, identity, or media input for analysis."],
            "engines_contributing": [],
            "certainty": "none",
            "calibrated_score": None,
            "honesty_note": (
                "Explainable Trust Score is a calibrated composite, not a guarantee."
            ),
        }

    # Weighted blend: emphasize highest risk while keeping average influence.
    scores = [item.risk_score for item in active]
    weights = [max(1, item.confidence) for item in active]
    weighted = sum(score * weight for score, weight in zip(scores, weights)) / max(sum(weights), 1)
    fused_risk = clamp(max(scores) * 0.65 + weighted * 0.35)
    trust_score = clamp(100 - fused_risk)

    threats: list[str] = []
    evidence: list[dict[str, Any]] = []
    recommendations: list[str] = []
    for item in active:
        for threat in item.threat_category:
            if threat not in threats:
                threats.append(threat)
        for ev in item.evidence[:3]:
            evidence.append({**ev, "engine_id": item.engine_id})
        for rec in item.recommendations[:2]:
            if rec not in recommendations:
                recommendations.append(rec)

    confidence = clamp(sum(item.confidence for item in active) / len(active))
    reasoning_en = (
        f"Fused {len(active)} active engines into risk {fused_risk}/100 "
        f"and trust {trust_score}/100. Highest engine risk was {max(scores)}."
    )
    reasoning_fr = (
        f"Fusion de {len(active)} moteurs actifs en risque {fused_risk}/100 "
        f"et confiance {trust_score}/100. Risque moteur max: {max(scores)}."
    )

    calibrated_score: int | None = None
    if calibration and calibration.get("ready"):
        calibrated_score = clamp(trust_score + int(calibration.get("bias_adjustment") or 0))

    return {
        "trust_score": trust_score,
        "trust_band": "high" if trust_score >= 70 else "medium" if trust_score >= 40 else "low",
        "fused_risk_score": fused_risk,
        "fused_risk_level": risk_band(fused_risk),
        "confidence": confidence,
        "calibrated_score": calibrated_score,
        "threat_categories": threats,
        "evidence": sorted(evidence, key=lambda item: item.get("weight", 0), reverse=True)[:12],
        "reasoning": reasoning_fr if lang.startswith("fr") else reasoning_en,
        "recommendations": recommendations[:6],
        "engines_contributing": [item.engine_id for item in active],
        "certainty": "none",
        "honesty_note": (
            "Explainable Trust Score combines modular engine signals. "
            "It is decision support, not absolute truth."
        ),
    }
