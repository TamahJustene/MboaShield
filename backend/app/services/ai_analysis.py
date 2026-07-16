"""Unified AI trust engine for MboaShield.

This layer turns raw detector outputs into a consistent AI analysis envelope:
- confidence
- threat taxonomy
- ranked evidence
- plain-language narrative
- next actions

Current engines are heuristic and explicitly ML-pluggable. The contract stays the
same when real models replace individual detectors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ENGINE_NAME = "mboashield-trust-engine"
ENGINE_VERSION = "0.5.0"

THREAT_TAXONOMY = {
    "disinformation": "False or unverified claims designed to spread panic or confusion",
    "social_engineering": "Pressure tactics that push urgent money or account actions",
    "impersonation": "Fake official identity, brand, or institutional authority",
    "voice_clone": "Synthetic or cloned voice risk in audio content",
    "synthetic_media": "Likely generated or heavily manipulated image content",
    "scam": "Fraud pattern aiming to extract money or credentials",
}


@dataclass
class AIAnalysis:
    engine: str
    engine_version: str
    modality: str
    risk_score: int
    risk_band: str
    confidence: int
    threat_categories: list[str]
    narrative: str
    evidence: list[dict[str, Any]] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    model_ready: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "engine_version": self.engine_version,
            "modality": self.modality,
            "risk_score": self.risk_score,
            "risk_band": self.risk_band,
            "confidence": self.confidence,
            "threat_categories": self.threat_categories,
            "threat_definitions": {
                key: THREAT_TAXONOMY[key] for key in self.threat_categories if key in THREAT_TAXONOMY
            },
            "narrative": self.narrative,
            "evidence": self.evidence,
            "next_actions": self.next_actions,
            "model_ready": self.model_ready,
            "honesty_note": (
                "Current detectors use calibrated heuristics with ML plug points. "
                "Confidence reflects signal consistency, not a black-box claim of certainty."
            ),
        }


def _band(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _clamp(score: int | float) -> int:
    return max(0, min(100, int(round(score))))


def _evidence_from_reasons(reasons: list[str], weight: int = 12) -> list[dict[str, Any]]:
    items = []
    for idx, reason in enumerate(reasons[:8]):
        items.append(
            {
                "id": f"ev-{idx + 1}",
                "label": reason,
                "weight": weight,
                "kind": "detector_signal",
            }
        )
    return items


def _confidence_from_signals(risk_score: int, signal_count: int, modality: str) -> int:
    base = 42
    if modality == "text":
        base = 48
    elif modality == "impersonation":
        base = 55
    elif modality in {"audio", "media"}:
        base = 40

    consistency = min(28, signal_count * 6)
    severity = int(risk_score * 0.22)
    return _clamp(base + consistency + severity)


def _threats_for_text(result: dict) -> list[str]:
    threats: list[str] = []
    joined = " ".join(result.get("reasons", [])).lower()
    source = result.get("source_verification") or {}
    if source.get("status") == "likely_scam" or source.get("scam_signals"):
        threats.append("scam")
    if any(token in joined for token in ["rumour", "urgent", "forward", "panic", "claim"]):
        threats.append("disinformation")
    if any(token in joined for token in ["money", "momo", "transfer", "account", "blocked"]):
        threats.append("social_engineering")
    if not threats and result.get("risk_score", 0) >= 40:
        threats.append("disinformation")
    return list(dict.fromkeys(threats))


def _threats_for_impersonation(result: dict) -> list[str]:
    threats = ["impersonation"]
    if result.get("risk_score", 0) >= 60:
        threats.append("scam")
    return threats


def _threats_for_audio(result: dict) -> list[str]:
    threats = ["voice_clone"]
    joined = " ".join(result.get("reasons", [])).lower()
    if "money" in joined or "official" in joined:
        threats.append("social_engineering")
    return threats


def _threats_for_media(result: dict) -> list[str]:
    return ["synthetic_media"]


def _narrative(modality: str, risk_band: str, threats: list[str], lang: str = "en") -> str:
    threat_text = ", ".join(threats) if threats else "general trust risk"
    if lang.startswith("fr"):
        mapping = {
            "high": f"Analyse IA: risque eleve ({threat_text}). Ne partagez pas et verifiez une source officielle.",
            "medium": f"Analyse IA: signaux mixtes ({threat_text}). Demandez une preuve et croisez les sources.",
            "low": f"Analyse IA: peu de signaux forts ({threat_text}). Restez prudent avant toute action.",
        }
    else:
        mapping = {
            "high": f"AI analysis: high risk ({threat_text}). Do not forward; verify via an official Cameroon source.",
            "medium": f"AI analysis: mixed signals ({threat_text}). Ask for proof and cross-check trusted sources.",
            "low": f"AI analysis: few strong signals ({threat_text}). Stay cautious before acting or sharing.",
        }
    return mapping[_band_safe(risk_band)]


def _band_safe(risk_band: str) -> str:
    if risk_band in {"high", "medium", "low"}:
        return risk_band
    return "low"


def _next_actions(modality: str, risk_band: str, lang: str = "en") -> list[str]:
    if lang.startswith("fr"):
        common = {
            "high": [
                "Ne transferrez pas d'argent et n'ouvrez aucun lien de paiement.",
                "Verifiez sur le site officiel de l'institution concernee.",
                "Signalez l'incident dans MboaShield pour revue.",
            ],
            "medium": [
                "Demandez la source originale avant de partager.",
                "Comparez avec un canal officiel FR/EN.",
                "Conservez une capture pour preuve.",
            ],
            "low": [
                "Restez vigilant et evitez le partage impulsif.",
                "Preferez les canaux officiels pour toute decision.",
            ],
        }
    else:
        common = {
            "high": [
                "Do not send money or open payment links.",
                "Verify on the official institution website.",
                "File an incident report in MboaShield for review.",
            ],
            "medium": [
                "Ask for the original source before sharing.",
                "Compare against an official FR/EN channel.",
                "Keep a screenshot as evidence.",
            ],
            "low": [
                "Stay alert and avoid impulsive forwarding.",
                "Prefer official channels for any decision.",
            ],
        }
    actions = list(common[_band_safe(risk_band)])
    if modality == "audio":
        actions.insert(0, "Call back using a known official number before trusting the voice note." if not lang.startswith("fr") else "Rappelez via un numero officiel connu avant de faire confiance a la note vocale.")
    if modality == "impersonation":
        actions.insert(0, "Compare the handle against the MboaShield institution registry." if not lang.startswith("fr") else "Comparez le compte au registre officiel MboaShield.")
    return actions[:4]


def enrich_result(result: dict, *, modality: str, lang: str = "en") -> dict:
    """Attach a standardized ai_analysis block to any detector result."""
    enriched = dict(result)
    risk_score = _clamp(enriched.get("risk_score", 0) or 0)
    risk_band = enriched.get("risk_band") or _band(risk_score)
    reasons = list(enriched.get("reasons") or [])

    if modality == "text":
        threats = _threats_for_text(enriched)
    elif modality == "impersonation":
        threats = _threats_for_impersonation(enriched)
    elif modality == "audio":
        threats = _threats_for_audio(enriched)
    elif modality == "media":
        threats = _threats_for_media(enriched)
    else:
        threats = []

    evidence = _evidence_from_reasons(reasons)
    source = enriched.get("source_verification") or {}
    for scam in source.get("scam_signals") or []:
        evidence.append(
            {
                "id": f"scam-{len(evidence) + 1}",
                "label": f"Scam lexicon hit: {scam}",
                "weight": 16,
                "kind": "source_signal",
            }
        )
    if enriched.get("matched_institution"):
        inst = enriched["matched_institution"]
        evidence.append(
            {
                "id": f"inst-{len(evidence) + 1}",
                "label": f"Institution proximity: {inst.get('short_name')} ({inst.get('name')})",
                "weight": 18,
                "kind": "registry_signal",
            }
        )

    analysis = AIAnalysis(
        engine=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        modality=modality,
        risk_score=risk_score,
        risk_band=_band_safe(risk_band),
        confidence=_confidence_from_signals(risk_score, len(evidence), modality),
        threat_categories=threats,
        narrative=_narrative(modality, risk_band, threats, lang),
        evidence=sorted(evidence, key=lambda item: item.get("weight", 0), reverse=True)[:10],
        next_actions=_next_actions(modality, risk_band, lang),
    )
    enriched["ai_analysis"] = analysis.as_dict()
    return enriched


def analyze_case(
    *,
    text: str = "",
    name: str = "",
    handle: str = "",
    lang: str = "en",
) -> dict[str, Any]:
    """Run a multi-signal case analysis for text + optional impersonation context."""
    from . import impersonation, source_verify, text_check

    modules: list[dict[str, Any]] = []
    text_result = None
    imp_result = None

    if text.strip():
        text_result = text_check.check_text(text, lang).as_dict()
        text_result["source_verification"] = source_verify.verify_claim(text, lang).as_dict()
        text_result = enrich_result(text_result, modality="text", lang=lang)
        modules.append({"modality": "text", "result": text_result})

    if name.strip() or handle.strip():
        imp_result = impersonation.check_impersonation(name, handle, lang).as_dict()
        imp_result = enrich_result(imp_result, modality="impersonation", lang=lang)
        modules.append({"modality": "impersonation", "result": imp_result})

    if not modules:
        empty = {
            "risk_score": 0,
            "risk_band": "low",
            "reasons": ["No content provided for analysis"],
            "advice": "Provide text and/or an account identity to analyse.",
        }
        return {
            "case_id": None,
            "overall": enrich_result(empty, modality="case", lang=lang)["ai_analysis"],
            "modules": [],
        }

    scores = [m["result"].get("risk_score", 0) for m in modules]
    overall_score = _clamp(max(scores) if len(scores) == 1 else (sum(scores) / len(scores)) * 0.35 + max(scores) * 0.65)
    threat_set: list[str] = []
    evidence: list[dict[str, Any]] = []
    for module in modules:
        analysis = module["result"].get("ai_analysis") or {}
        for threat in analysis.get("threat_categories", []):
            if threat not in threat_set:
                threat_set.append(threat)
        for item in analysis.get("evidence", [])[:4]:
            evidence.append({**item, "modality": module["modality"]})

    overall_band = _band(overall_score)
    overall = AIAnalysis(
        engine=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        modality="case",
        risk_score=overall_score,
        risk_band=overall_band,
        confidence=_confidence_from_signals(overall_score, len(evidence), "case"),
        threat_categories=threat_set,
        narrative=_narrative("case", overall_band, threat_set, lang),
        evidence=sorted(evidence, key=lambda item: item.get("weight", 0), reverse=True)[:12],
        next_actions=_next_actions("case", overall_band, lang),
    ).as_dict()

    return {
        "modules": modules,
        "overall": overall,
        "summary": {
            "module_count": len(modules),
            "max_module_score": max(scores),
            "threat_categories": threat_set,
        },
    }
