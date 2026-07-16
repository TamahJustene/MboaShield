from __future__ import annotations

from .. import source_verify
from .base import EngineResult, clamp, risk_band, skipped


def analyze(*, text: str = "", lang: str = "en") -> EngineResult:
    if not (text or "").strip():
        return skipped("source_intelligence", "Source Intelligence", "No claim text provided.")

    raw = source_verify.verify_claim(text, lang).as_dict()
    status = raw.get("status") or "unknown"
    scam = list(raw.get("scam_signals") or [])
    matched = list(raw.get("matched_sources") or [])

    score = 15
    threats: list[str] = []
    if status == "likely_scam" or scam:
        score = 78
        threats.append("scam")
    elif status == "unverified":
        score = 48
        threats.append("disinformation")
    elif status == "supported":
        score = 18

    evidence = [{"label": f"Source status: {status}", "weight": 14, "kind": "source_signal"}]
    for item in scam[:5]:
        evidence.append({"label": f"Scam lexicon: {item}", "weight": 16, "kind": "scam_signal"})
    for item in matched[:3]:
        evidence.append(
            {
                "label": f"Matched source: {item.get('name') or item}",
                "weight": 12,
                "kind": "corpus_match",
            }
        )

    return EngineResult(
        engine_id="source_intelligence",
        engine_name="Source Intelligence",
        confidence=clamp(50 + len(evidence) * 4),
        evidence=evidence,
        reasoning=raw.get("summary") or "Claim checked against local official-source corpus and scam lexicon.",
        risk_level=risk_band(score),
        risk_score=score,
        threat_category=threats,
        recommendations=[
            "Prefer official .gov or verified institutional pages.",
            "Treat unsupported viral claims as unverified until confirmed.",
        ],
        details={"source_verification": raw},
    )
