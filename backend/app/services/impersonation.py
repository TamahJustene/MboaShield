"""Institutional impersonation checks against local registry."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass

from ..config import DATA_DIR


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9@\s_]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s


@dataclass
class ImpersonationResult:
    risk_score: int
    risk_band: str
    is_suspicious: bool
    matched_institution: dict | None
    reasons: list[str]
    advice: str

    def as_dict(self) -> dict:
        return {
            "risk_score": self.risk_score,
            "risk_band": self.risk_band,
            "is_suspicious": self.is_suspicious,
            "matched_institution": self.matched_institution,
            "reasons": self.reasons,
            "advice": self.advice,
        }


def _band(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _load_institutions() -> list[dict]:
    try:
        from ..repositories import list_institutions

        items = list_institutions()
        if items:
            return items
    except Exception:
        pass
    return json.loads((DATA_DIR / "institutions.json").read_text(encoding="utf-8"))


def check_impersonation(name: str, handle: str = "", lang: str = "en") -> ImpersonationResult:
    query_parts = [_norm(name), _norm(handle)]
    query = " ".join(p for p in query_parts if p)
    if not query:
        return ImpersonationResult(
            risk_score=0,
            risk_band="low",
            is_suspicious=False,
            matched_institution=None,
            reasons=["Empty name/handle"],
            advice="Provide an account name or handle to check.",
        )

    institutions = _load_institutions()
    best = None
    best_score = 0
    reasons: list[str] = []

    spoof_tokens = ["officiel", "official", "verifie", "verified", "vraie", "real", "cm__", "info_"]
    spoof_hits = [t for t in spoof_tokens if t in query]
    if spoof_hits:
        best_score += 25
        reasons.append(f"Spoof-style tokens detected: {', '.join(spoof_hits)}")

    for inst in institutions:
        candidates = [_norm(inst["name"]), _norm(inst["short_name"])] + [
            _norm(h) for h in inst.get("handles", [])
        ]
        for cand in candidates:
            if not cand:
                continue
            if cand in query or query in cand:
                score = 55
                if cand == query:
                    score = 20  # exact verified-looking match ? lower spoof risk if no spoof tokens
                # Near match with extras ? impersonation pattern
                if cand in query and cand != query:
                    score = 80
                if score > best_score:
                    best_score = score
                    best = inst
                    reasons.append(
                        f"Close to verified institution ?{inst['short_name']}? ({inst['name']})"
                    )

    # If exact official handle with no spoof tokens ? low risk
    if best and best_score <= 25 and not spoof_hits:
        advice = (
            "Looks aligned with a known institution; still prefer the official website."
            if not lang.startswith("fr")
            else "Correspond ? une institution connue ; pr?f?rez tout de m?me le site officiel."
        )
        return ImpersonationResult(
            risk_score=best_score,
            risk_band=_band(best_score),
            is_suspicious=False,
            matched_institution=best,
            reasons=reasons or ["Possible legitimate institutional reference"],
            advice=advice,
        )

    score = max(0, min(100, best_score if best_score else (35 if spoof_hits else 15)))
    suspicious = score >= 40
    if lang.startswith("fr"):
        advice = (
            "Compte potentiellement usurp?. Comparez avec le site officiel et ne cliquez sur aucun lien de paiement."
            if suspicious
            else "Pas de fort signal d'usurpation, mais v?rifiez toujours le canal officiel."
        )
    else:
        advice = (
            "Possible impersonation. Compare with the official website and never follow payment links."
            if suspicious
            else "No strong impersonation signal, but always confirm the official channel."
        )

    return ImpersonationResult(
        risk_score=score,
        risk_band=_band(score),
        is_suspicious=suspicious,
        matched_institution=best,
        reasons=reasons[:6] or ["No close institutional match"],
        advice=advice,
    )
