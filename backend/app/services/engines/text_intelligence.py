from __future__ import annotations

from typing import Any

from .. import text_check
from .base import EngineResult, clamp, risk_band


def analyze(*, text: str = "", lang: str = "en") -> EngineResult:
    if not (text or "").strip():
        from .base import skipped

        return skipped("text_intelligence", "Text Intelligence", "No text provided.")

    raw = text_check.check_text(text, lang).as_dict()
    score = clamp(raw.get("risk_score", 0) or 0)
    nlp = raw.get("nlp") or {}
    evidence = [{"label": reason, "weight": 12, "kind": "text_signal"} for reason in raw.get("reasons", [])[:6]]
    if nlp.get("top_features"):
        for feature in nlp["top_features"][:3]:
            evidence.append(
                {
                    "label": f"NLP feature: {feature.get('name')} ({feature.get('value')})",
                    "weight": 10,
                    "kind": "nlp_signal",
                }
            )

    threats: list[str] = []
    joined = " ".join(raw.get("reasons", [])).lower()
    if any(token in joined for token in ["rumour", "urgent", "forward", "panic", "claim"]):
        threats.append("disinformation")
    if any(token in joined for token in ["money", "momo", "transfer", "account", "blocked"]):
        threats.append("social_engineering")
    if score >= 40 and not threats:
        threats.append("disinformation")

    return EngineResult(
        engine_id="text_intelligence",
        engine_name="Text Intelligence",
        confidence=clamp(48 + min(30, len(evidence) * 5) + score * 0.15),
        evidence=evidence,
        reasoning=raw.get("advice")
        or "Text patterns were scored using hybrid NLP and heuristic rumour signals.",
        risk_level=risk_band(score),
        risk_score=score,
        threat_category=threats,
        recommendations=[raw.get("advice") or "Verify before sharing.", "Do not forward unverified claims."],
        details={"backend": raw.get("backend"), "nlp": nlp, "raw_score": score},
    )
