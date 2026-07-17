"""National TrustAssessment bridge (T1) - wraps checks and intelligence fusion."""

from __future__ import annotations

from typing import Any

from ..repositories import get_verification_check, save_verification_check
from ..services import impersonation, source_verify, text_check
from ..services.ai_analysis import analyze_case, enrich_result
from ..services.engines import analyze_intelligence
from ..services.model_adapters import analyze_audio_with_fallback, analyze_image_with_fallback
from ..trust_store import save_trust_assessment

ALLOWED_OBJECT_TYPES = {
    "text",
    "impersonation",
    "media",
    "audio",
    "intelligence",
    "case",
    "verification_check",
}


def trust_band_from_score(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def trust_from_risk(risk_score: int | None) -> tuple[int, str]:
    risk = 50 if risk_score is None else int(risk_score)
    score = max(0, min(100, 100 - risk))
    return score, trust_band_from_score(score)


def signals_from_check_result(result: dict) -> list[dict]:
    signals: list[dict] = []
    for reason in result.get("reasons") or []:
        signals.append({"type": "reason", "label": str(reason), "weight": None})
    source = result.get("source_verification") or {}
    for scam in source.get("scam_signals") or []:
        signals.append({"type": "scam_signal", "label": str(scam), "weight": None})
    analysis = result.get("ai_analysis") or {}
    for threat in analysis.get("threat_categories") or []:
        signals.append(
            {
                "type": "threat_category",
                "label": str(threat),
                "weight": analysis.get("confidence"),
            }
        )
    trust = result.get("trust_score")
    if isinstance(trust, dict):
        for ev in trust.get("evidence") or []:
            signals.append(
                {
                    "type": "engine_evidence",
                    "label": str(ev.get("summary") or ev.get("kind") or "signal"),
                    "weight": ev.get("weight"),
                }
            )
    return signals[:24]


def evidence_refs_from_result(
    *,
    verification_check_id: int | None,
    engines: list[str] | None = None,
) -> list[dict]:
    refs: list[dict] = []
    if verification_check_id is not None:
        refs.append(
            {
                "ref_type": "verification_check",
                "id": str(verification_check_id),
                "label": f"Verification check #{verification_check_id}",
            }
        )
    for engine_id in engines or []:
        refs.append({"ref_type": "engine", "id": engine_id, "label": engine_id})
    return refs


def build_assessment_envelope(
    *,
    object_type: str,
    object_id: str | None,
    score: int,
    band: str,
    certainty: str,
    signals: list[dict],
    evidence_refs: list[dict],
    legacy: dict[str, Any],
    assessment_id: int | None = None,
    verification_check_id: int | None = None,
) -> dict[str, Any]:
    return {
        "id": assessment_id,
        "object_type": object_type,
        "object_id": object_id,
        "score": score,
        "band": band,
        "certainty": certainty,
        "signals": signals,
        "evidence_refs": evidence_refs,
        "verification_check_id": verification_check_id,
        "legacy": legacy,
        "honesty_note": (
            "Trust assessments are explainable decision support. "
            "They never claim absolute certainty."
        ),
    }


def assess_verification_check(check_id: int, *, persist: bool = True) -> dict[str, Any]:
    check = get_verification_check(check_id)
    if not check:
        raise ValueError("verification_check not found")
    result = check.get("result") or {}
    trust_block = result.get("trust_score")
    if isinstance(trust_block, dict) and trust_block.get("trust_score") is not None:
        score = int(trust_block["trust_score"])
        band = trust_block.get("trust_band") or trust_band_from_score(score)
        certainty = trust_block.get("certainty") or "none"
        engines = trust_block.get("engines_contributing") or []
    else:
        score, band = trust_from_risk(check.get("risk_score"))
        certainty = "none"
        engines = []
    signals = signals_from_check_result(result)
    if not signals and check.get("signals"):
        for row in check["signals"]:
            signals.append(
                {
                    "type": row.get("signal_type") or "signal",
                    "label": row.get("signal_label") or "",
                    "weight": row.get("signal_score"),
                }
            )
    evidence_refs = evidence_refs_from_result(
        verification_check_id=check_id,
        engines=engines,
    )
    legacy = {
        "risk_score": check.get("risk_score"),
        "risk_band": check.get("risk_band"),
        "check_type": check.get("check_type"),
        "result": result,
    }
    assessment_id = None
    if persist:
        assessment_id = save_trust_assessment(
            object_type="verification_check",
            object_id=str(check_id),
            score=score,
            band=band,
            certainty=certainty,
            signals=signals,
            evidence_refs=evidence_refs,
            verification_check_id=check_id,
            payload=legacy,
            lang=check.get("input", {}).get("lang") or "en",
            user_id=check.get("user_id"),
        )
    return build_assessment_envelope(
        object_type="verification_check",
        object_id=str(check_id),
        score=score,
        band=band,
        certainty=certainty,
        signals=signals,
        evidence_refs=evidence_refs,
        legacy=legacy,
        assessment_id=assessment_id,
        verification_check_id=check_id,
    )


def assess_text(*, text: str, lang: str, user_id: int | None, persist: bool) -> dict[str, Any]:
    result = text_check.check_text(text, lang).as_dict()
    result["source_verification"] = source_verify.verify_claim(text, lang).as_dict()
    result = enrich_result(result, modality="text", lang=lang)
    check_id = save_verification_check(
        check_type="text",
        result=result,
        lang=lang,
        input_text=text,
        user_id=user_id,
    )
    result["check_id"] = check_id
    score, band = trust_from_risk(result.get("risk_score"))
    signals = signals_from_check_result(result)
    evidence_refs = evidence_refs_from_result(verification_check_id=check_id)
    assessment_id = None
    if persist:
        assessment_id = save_trust_assessment(
            object_type="text",
            object_id=str(check_id),
            score=score,
            band=band,
            certainty="none",
            signals=signals,
            evidence_refs=evidence_refs,
            verification_check_id=check_id,
            payload=result,
            lang=lang,
            user_id=user_id,
        )
    envelope = build_assessment_envelope(
        object_type="text",
        object_id=str(check_id),
        score=score,
        band=band,
        certainty="none",
        signals=signals,
        evidence_refs=evidence_refs,
        legacy=result,
        assessment_id=assessment_id,
        verification_check_id=check_id,
    )
    envelope["risk_score"] = result.get("risk_score")
    envelope["risk_band"] = result.get("risk_band")
    envelope["check_id"] = check_id
    return envelope


def assess_impersonation(
    *, name: str, handle: str, lang: str, user_id: int | None, persist: bool
) -> dict[str, Any]:
    result = impersonation.check_impersonation(name, handle, lang).as_dict()
    result = enrich_result(result, modality="impersonation", lang=lang)
    check_id = save_verification_check(
        check_type="impersonation",
        result=result,
        lang=lang,
        input_text=name,
        input_handle=handle,
        user_id=user_id,
    )
    result["check_id"] = check_id
    score, band = trust_from_risk(result.get("risk_score"))
    signals = signals_from_check_result(result)
    evidence_refs = evidence_refs_from_result(verification_check_id=check_id)
    assessment_id = None
    if persist:
        assessment_id = save_trust_assessment(
            object_type="impersonation",
            object_id=str(check_id),
            score=score,
            band=band,
            certainty="none",
            signals=signals,
            evidence_refs=evidence_refs,
            verification_check_id=check_id,
            payload=result,
            lang=lang,
            user_id=user_id,
        )
    envelope = build_assessment_envelope(
        object_type="impersonation",
        object_id=str(check_id),
        score=score,
        band=band,
        certainty="none",
        signals=signals,
        evidence_refs=evidence_refs,
        legacy=result,
        assessment_id=assessment_id,
        verification_check_id=check_id,
    )
    envelope["risk_score"] = result.get("risk_score")
    envelope["risk_band"] = result.get("risk_band")
    envelope["check_id"] = check_id
    return envelope


def assess_media_bytes(
    *, data: bytes, filename: str, lang: str, user_id: int | None, persist: bool
) -> dict[str, Any]:
    result = analyze_image_with_fallback(data, filename=filename, lang=lang)
    result = enrich_result(result, modality="media", lang=lang)
    check_id = save_verification_check(
        check_type="media",
        result=result,
        lang=lang,
        input_filename=filename,
        user_id=user_id,
    )
    result["check_id"] = check_id
    score, band = trust_from_risk(result.get("risk_score"))
    signals = signals_from_check_result(result)
    evidence_refs = evidence_refs_from_result(verification_check_id=check_id)
    assessment_id = None
    if persist:
        assessment_id = save_trust_assessment(
            object_type="media",
            object_id=str(check_id),
            score=score,
            band=band,
            certainty="none",
            signals=signals,
            evidence_refs=evidence_refs,
            verification_check_id=check_id,
            payload=result,
            lang=lang,
            user_id=user_id,
        )
    envelope = build_assessment_envelope(
        object_type="media",
        object_id=str(check_id),
        score=score,
        band=band,
        certainty="none",
        signals=signals,
        evidence_refs=evidence_refs,
        legacy=result,
        assessment_id=assessment_id,
        verification_check_id=check_id,
    )
    envelope["risk_score"] = result.get("risk_score")
    envelope["risk_band"] = result.get("risk_band")
    envelope["check_id"] = check_id
    return envelope


def assess_audio_bytes(
    *, data: bytes, filename: str, lang: str, user_id: int | None, persist: bool
) -> dict[str, Any]:
    result = analyze_audio_with_fallback(data, filename=filename, lang=lang)
    result = enrich_result(result, modality="audio", lang=lang)
    check_id = save_verification_check(
        check_type="audio",
        result=result,
        lang=lang,
        input_filename=filename,
        user_id=user_id,
    )
    result["check_id"] = check_id
    score, band = trust_from_risk(result.get("risk_score"))
    signals = signals_from_check_result(result)
    evidence_refs = evidence_refs_from_result(verification_check_id=check_id)
    assessment_id = None
    if persist:
        assessment_id = save_trust_assessment(
            object_type="audio",
            object_id=str(check_id),
            score=score,
            band=band,
            certainty="none",
            signals=signals,
            evidence_refs=evidence_refs,
            verification_check_id=check_id,
            payload=result,
            lang=lang,
            user_id=user_id,
        )
    envelope = build_assessment_envelope(
        object_type="audio",
        object_id=str(check_id),
        score=score,
        band=band,
        certainty="none",
        signals=signals,
        evidence_refs=evidence_refs,
        legacy=result,
        assessment_id=assessment_id,
        verification_check_id=check_id,
    )
    envelope["risk_score"] = result.get("risk_score")
    envelope["risk_band"] = result.get("risk_band")
    envelope["check_id"] = check_id
    return envelope


def assess_intelligence(
    *,
    text: str = "",
    name: str = "",
    handle: str = "",
    url: str = "",
    filename: str = "",
    mime_type: str = "",
    size_bytes: int | None = None,
    image_bytes: bytes | None = None,
    audio_bytes: bytes | None = None,
    lang: str = "en",
    include_scaffolds: bool = True,
    user_id: int | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    intel = analyze_intelligence(
        text=text,
        name=name,
        handle=handle,
        url=url,
        filename=filename,
        mime_type=mime_type,
        size_bytes=size_bytes,
        image_bytes=image_bytes,
        audio_bytes=audio_bytes,
        lang=lang,
        include_scaffolds=include_scaffolds,
    )
    trust = intel.get("trust_score") or {}
    if intel.get("risk_score") is None:
        fused = trust.get("fused_risk_score")
        if fused is None and trust.get("trust_score") is not None:
            fused = max(0, min(100, 100 - int(trust["trust_score"])))
        intel["risk_score"] = fused if fused is not None else 50
        intel["risk_band"] = trust.get("fused_risk_level") or trust.get("trust_band") or "medium"
    score = int(trust.get("trust_score") or 50)
    band = trust.get("trust_band") or trust_band_from_score(score)
    certainty = trust.get("certainty") or "none"
    signals = signals_from_check_result({"trust_score": trust, "ai_analysis": intel.get("summary")})
    if not signals:
        for engine in intel.get("engines") or []:
            if engine.get("status") != "ok":
                continue
            signals.append(
                {
                    "type": "engine",
                    "label": f"{engine.get('engine_id')}: {engine.get('risk_level')}",
                    "weight": engine.get("confidence"),
                }
            )
    engines = trust.get("engines_contributing") or []
    check_id = save_verification_check(
        check_type="intelligence",
        result=intel,
        lang=lang,
        input_text=text,
        input_handle=handle,
        input_filename=filename,
        user_id=user_id,
    )
    evidence_refs = evidence_refs_from_result(verification_check_id=check_id, engines=engines)
    assessment_id = None
    if persist:
        assessment_id = save_trust_assessment(
            object_type="intelligence",
            object_id=str(check_id),
            score=score,
            band=band,
            certainty=certainty,
            signals=signals,
            evidence_refs=evidence_refs,
            verification_check_id=check_id,
            payload=intel,
            lang=lang,
            user_id=user_id,
        )
    envelope = build_assessment_envelope(
        object_type="intelligence",
        object_id=str(check_id),
        score=score,
        band=band,
        certainty=certainty,
        signals=signals,
        evidence_refs=evidence_refs,
        legacy=intel,
        assessment_id=assessment_id,
        verification_check_id=check_id,
    )
    envelope["check_id"] = check_id
    envelope["trust_score"] = trust
    return envelope


def assess_case(
    *,
    text: str,
    name: str,
    handle: str,
    lang: str,
    user_id: int | None,
    persist: bool,
) -> dict[str, Any]:
    case = analyze_case(text=text, name=name, handle=handle, lang=lang)
    check_id = None
    for module in case.get("modules", []):
        modality = module["modality"]
        result = module["result"]
        if modality == "text":
            check_id = save_verification_check(
                check_type="text",
                result=result,
                lang=lang,
                input_text=text,
                user_id=user_id,
            )
            result["check_id"] = check_id
        elif modality == "impersonation":
            saved = save_verification_check(
                check_type="impersonation",
                result=result,
                lang=lang,
                input_text=name,
                input_handle=handle,
                user_id=user_id,
            )
            result["check_id"] = saved
            if check_id is None:
                check_id = saved
    case["case_check_id"] = check_id

    trust = case.get("trust_score") or {}
    overall = case.get("overall") or {}
    if trust.get("trust_score") is not None:
        score = int(trust["trust_score"])
        band = trust.get("trust_band") or trust_band_from_score(score)
    else:
        score, band = trust_from_risk(overall.get("risk_score"))
    certainty = trust.get("certainty") or "none"
    signals = signals_from_check_result({**case, "ai_analysis": overall})
    engines = trust.get("engines_contributing") or []
    evidence_refs = evidence_refs_from_result(verification_check_id=check_id, engines=engines)
    assessment_id = None
    if persist:
        assessment_id = save_trust_assessment(
            object_type="case",
            object_id=str(check_id) if check_id else None,
            score=score,
            band=band,
            certainty=certainty,
            signals=signals,
            evidence_refs=evidence_refs,
            verification_check_id=check_id,
            payload=case,
            lang=lang,
            user_id=user_id,
        )
    envelope = build_assessment_envelope(
        object_type="case",
        object_id=str(check_id) if check_id else None,
        score=score,
        band=band,
        certainty=certainty,
        signals=signals,
        evidence_refs=evidence_refs,
        legacy=case,
        assessment_id=assessment_id,
        verification_check_id=check_id,
    )
    envelope["case_check_id"] = check_id
    return envelope
