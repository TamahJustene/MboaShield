"""Text / rumour risk scoring with NLP model path + heuristic blend."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from ..config import DATA_DIR
from .nlp_text import score_text_nlp

HIGH_RISK_PATTERNS = [
    r"envoie\s*(de\s*)?l[' ]?argent",
    r"send\s*money",
    r"transfert\s*urgent",
    r"urgent\s*transfer",
    r"\bmomo\b|mtn\s*momo|orange\s*money",
    r"compte\s*bloqu",
    r"account\s*blocked",
    r"gagn[ea]?\s*(un\s*)?(million|voiture|iphone)",
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
    r"transfer[e]?\s*plein\s*de\s*fois",
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
    nlp: dict | None = None
    engine: str = "text-hybrid-v1"
    backend: str = "nlp+heuristic"

    def as_dict(self) -> dict:
        payload = {
            "risk_score": self.risk_score,
            "risk_band": self.risk_band,
            "reasons": self.reasons,
            "suggested_sources": self.suggested_sources,
            "advice": self.advice,
            "engine": self.engine,
            "backend": self.backend,
        }
        if self.nlp:
            payload["nlp"] = self.nlp
        return payload


def _load_sources() -> list[dict]:
    path = DATA_DIR / "sources.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _band(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _heuristic_score(text: str) -> tuple[int, list[str]]:
    lowered = text.lower()
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

    if len(text) > 40 and not re.search(r"https?://|www\.", lowered):
        score += 6
        reasons.append("Long claim without any source link")

    if re.search(r"[A-Z]{6,}", text) and sum(1 for c in text if c.isupper()) > len(text) * 0.35:
        score += 10
        reasons.append("Heavy shout-casing often used in panic forwards")

    return max(0, min(100, score)), reasons


def check_text(text: str, lang: str = "en") -> TextCheckResult:
    raw = (text or "").strip()
    if not raw:
        return TextCheckResult(
            risk_score=0,
            risk_band="low",
            reasons=["Empty text"],
            suggested_sources=[],
            advice="Paste a WhatsApp message or rumour to analyse.",
            backend="empty",
        )

    heuristic_score, heuristic_reasons = _heuristic_score(raw)
    nlp = score_text_nlp(raw)
    nlp_score = int(nlp.get("risk_score", 0))

    # Prefer agreement: blend NLP model with pattern heuristics.
    blended = int(round(nlp_score * 0.55 + heuristic_score * 0.45))
    if abs(nlp_score - heuristic_score) >= 25:
        blended = int(round(max(nlp_score, heuristic_score) * 0.7 + min(nlp_score, heuristic_score) * 0.3))
    score = max(0, min(100, blended))

    reasons = list(dict.fromkeys((nlp.get("reasons") or [])[:4] + heuristic_reasons))[:8]
    if not reasons:
        reasons.append("No strong rumour markers; still verify before forwarding")

    lowered = raw.lower()
    sources = _load_sources()
    suggested = []
    for src in sources:
        if any(t in lowered for t in src.get("topics", [])):
            suggested.append(src)
    if not suggested:
        suggested = sources[:2]

    if lang.startswith("fr"):
        advice = {
            "high": "Risque eleve. Ne transferrez pas. Verifiez une source officielle camerounaise.",
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
        reasons=reasons,
        suggested_sources=suggested[:3],
        advice=advice,
        nlp=nlp,
        engine="text-hybrid-v1",
        backend="nlp+heuristic",
    )
