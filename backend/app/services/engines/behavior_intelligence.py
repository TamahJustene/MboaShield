from __future__ import annotations

import re

from .base import EngineResult, clamp, risk_band, skipped

PRESSURE_PATTERNS = [
    r"\burgent\b",
    r"immediately",
    r"right\s*now",
    r"avant\s*qu",
    r"tout\s*de\s*suite",
    r"do\s*not\s*tell",
    r"ne\s*dis\s*a\s*personne",
    r"secret",
    r"last\s*chance",
    r"act\s*now",
]


def analyze(*, text: str = "", lang: str = "en") -> EngineResult:
    if not (text or "").strip():
        return skipped("behavior_intelligence", "Behavior Intelligence", "No text provided for behavior cues.")

    lowered = text.lower()
    hits = [pattern for pattern in PRESSURE_PATTERNS if re.search(pattern, lowered, flags=re.I)]
    score = clamp(20 + len(hits) * 14)
    evidence = [{"label": f"Pressure pattern: {hit}", "weight": 13, "kind": "behavior_signal"} for hit in hits[:6]]
    threats = ["social_engineering"] if hits else []

    return EngineResult(
        engine_id="behavior_intelligence",
        engine_name="Behavior Intelligence",
        confidence=clamp(45 + len(hits) * 8),
        evidence=evidence,
        reasoning=(
            "Message pressure and secrecy cues were scanned for social-engineering behavior."
            if hits
            else "No strong urgency or secrecy pressure patterns were detected."
        ),
        risk_level=risk_band(score),
        risk_score=score,
        threat_category=threats,
        recommendations=[
            "Pause before acting on urgent private requests.",
            "Verify through a second trusted channel.",
        ],
        details={"pressure_hits": hits},
    )
