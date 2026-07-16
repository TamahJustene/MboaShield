from __future__ import annotations

from .. import impersonation
from .base import EngineResult, clamp, risk_band, skipped


def analyze(*, name: str = "", handle: str = "", lang: str = "en") -> EngineResult:
    if not (name or "").strip() and not (handle or "").strip():
        return skipped("identity_intelligence", "Identity Intelligence", "No account identity provided.")

    raw = impersonation.check_impersonation(name, handle, lang).as_dict()
    score = clamp(raw.get("risk_score", 0) or 0)
    evidence = [{"label": reason, "weight": 14, "kind": "identity_signal"} for reason in raw.get("reasons", [])[:6]]
    matched = raw.get("matched_institution")
    if matched:
        evidence.append(
            {
                "label": f"Registry proximity: {matched.get('short_name')} ({matched.get('name')})",
                "weight": 18,
                "kind": "registry_signal",
            }
        )

    threats = ["impersonation"] if score >= 40 or raw.get("is_suspicious") else []
    return EngineResult(
        engine_id="identity_intelligence",
        engine_name="Identity Intelligence",
        confidence=clamp(55 + min(25, len(evidence) * 5)),
        evidence=evidence,
        reasoning=raw.get("advice")
        or "Account name/handle compared against the institution registry and spoof patterns.",
        risk_level=risk_band(score),
        risk_score=score,
        threat_category=threats,
        recommendations=[
            "Compare the handle against the MboaShield institution registry.",
            "Do not send money or credentials to unverified accounts.",
        ],
        details={"matched_institution": matched, "is_suspicious": raw.get("is_suspicious")},
    )
