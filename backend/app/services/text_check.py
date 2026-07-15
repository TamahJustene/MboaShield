"""Text / rumour risk scoring (heuristic v0  ML-pluggable)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from ..config import DATA_DIR

HIGH_RISK_PATTERNS = [
    r"envoie\s*(de\s*)?l[' ]?argent",
    r"send\s*money",
    r"transfert\s*urgent",
    r"urgent\s*transfer",
    r"\bmomo\b|mtn\s*momo|orange\s*money",
    r"compte\s*bloqu",
    r"account\s*blocked",
    r"gagn[eé]?\s*(un\s*)?(million|voiture|iphone)",
    r"you\s*won\s*(a\s*)?(million|car|iphone)",
    r"ministre\s*annonce",
    r"minister\s*announces",
    r"couvre[- ]feu",
    r"nationwide\s*curfew",
    r"fermeture\s*des?\s*banques",
    r"banks?\s*(are\s*)?closed",
    r"\burgent\b",
]

UNCERTAINTY_PATTERNS = [
    r"on\s*dit\s*que",
    r"ils?\s*disent",
    r"people\s*say",
    r"forwarded\s*many\s*times",
    r"transf[e]r[e]\s*plein\s*de\s*fois",
    r"share\s*before\s*it'?s\s*deleted",
    r"partage\s*avant\s*suppression",
]


@dataclass
class TextCheckResult:
    risk_score: int
    risk_band: str
    reasons: list[str]
    suggested_sources: list[dict]
    advice: str

    def as_dict(self) -> dict:
        return {
            "risk_score": self.risk_score,
            "risk_band": self.risk_band,
            "reasons": self.reasons,
            "suggested_sources": self.suggested_sources,
            "advice": self.advice,
        }


def _load_sources() -> list[dict]:
    path = DATA_DIR / "sources.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _band(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def check_text(text: str, lang: str = "en") -> TextCheckResult:
    raw = (text or "").strip()
    if not raw:
        return TextCheckResult(
            risk_score=0,
            risk_band="low",
            reasons=["Empty text"],
            suggested_sources=[],
            advice="Paste a WhatsApp message or rumour to analyse.",
        )

    lowered = raw.lower()
    score = 10
    reasons: list[str] = []

    for pattern in HIGH_RISK_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            score += 18
            reasons.append(f"Matched high-risk pattern: /{pattern}/")

    for pattern in UNCERTAINTY_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            score += 8
            reasons.append(f"Matched rumour-style phrasing: /{pattern}/")

    if len(raw) > 40 and not re.search(r"https?://|www\.", lowered):
        score += 6
        reasons.append("Long claim without any source link")

    if re.search(r"[A-Z]{6,}", raw) and sum(
        1 for c in raw if c.isupper()
    ) > len(raw) * 0.35:
        score += 10
        reasons.append("Heavy shout-casing often used in panic forwards")

    score = max(0, min(100, score))
    if not reasons:
        reasons.append("No strong rumour markers; still verify before forwarding")

    sources = _load_sources()
    # simple topic overlap
    suggested = []
    for src in sources:
        if any(t in lowered for t in src.get("topics", [])):
            suggested.append(src)
    if not suggested:
        suggested = sources[:2]

    if lang.startswith("fr"):
        advice = {
            "high": "Risque lev. Ne transfrez pas. Vrifiez une source officielle camerounaise.",
            "medium": "Risque moyen. Demandez une preuve et consultez une source officielle.",
            "low": "Risque bas apparent, mais restez vigilant avant de partager.",
        }[_band(score)]
    else:
        advice = {
            "high": "High risk. Do not forward. Verify with an official Cameroonian source.",
            "medium": "Medium risk. Ask for proof and check an official source.",
            "low": "Apparently low risk, but stay careful before sharing.",
        }[_band(score)]

    return TextCheckResult(
        risk_score=score,
        risk_band=_band(score),
        reasons=reasons[:8],
        suggested_sources=suggested[:3],
        advice=advice,
    )
