"""National TrustAssessment API (MboaShield 2030 T1)."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ...core.openapi_pillars import PILLAR_TRUST
from ...schemas import TrustAssessIn, TrustAssessmentOut
from ...services.trust_assessment import (
    ALLOWED_OBJECT_TYPES,
    assess_audio_bytes,
    assess_case,
    assess_impersonation,
    assess_intelligence,
    assess_media_bytes,
    assess_text,
    assess_verification_check,
)
from ...trust_store import get_trust_assessment
from ..deps import LegacyUserId

router = APIRouter(prefix="/trust", tags=[PILLAR_TRUST])


@router.post("/assess", response_model=TrustAssessmentOut)
def api_trust_assess(body: TrustAssessIn, user_id: LegacyUserId):
    if body.object_type not in ALLOWED_OBJECT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported object_type: {body.object_type}")

    try:
        if body.object_type == "verification_check":
            if body.verification_check_id is None:
                raise HTTPException(status_code=400, detail="verification_check_id required")
            return assess_verification_check(body.verification_check_id, persist=body.persist)
        if body.object_type == "text":
            if not body.text.strip():
                raise HTTPException(status_code=400, detail="text required")
            return assess_text(text=body.text, lang=body.lang, user_id=user_id, persist=body.persist)
        if body.object_type == "impersonation":
            if not body.name.strip() and not body.handle.strip():
                raise HTTPException(status_code=400, detail="name or handle required")
            return assess_impersonation(
                name=body.name,
                handle=body.handle,
                lang=body.lang,
                user_id=user_id,
                persist=body.persist,
            )
        if body.object_type == "intelligence":
            if not any(
                [
                    body.text.strip(),
                    body.name.strip(),
                    body.handle.strip(),
                    body.url.strip(),
                    body.filename.strip(),
                ]
            ):
                raise HTTPException(status_code=400, detail="Provide intelligence context fields")
            return assess_intelligence(
                text=body.text,
                name=body.name,
                handle=body.handle,
                url=body.url,
                filename=body.filename,
                mime_type=body.mime_type,
                lang=body.lang,
                include_scaffolds=body.include_scaffolds,
                user_id=user_id,
                persist=body.persist,
            )
        if body.object_type == "case":
            if not body.text.strip() and not body.name.strip() and not body.handle.strip():
                raise HTTPException(status_code=400, detail="Provide text and/or identity fields")
            return assess_case(
                text=body.text,
                name=body.name,
                handle=body.handle,
                lang=body.lang,
                user_id=user_id,
                persist=body.persist,
            )
        raise HTTPException(status_code=400, detail="Use /trust/assess/media for media and audio types")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/assess/media", response_model=TrustAssessmentOut)
async def api_trust_assess_media(
    user_id: LegacyUserId,
    file: UploadFile = File(...),
    lang: str = Form("en"),
    modality: str = Form("image"),
    persist: bool = Form(True),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > 12_000_000:
        raise HTTPException(status_code=400, detail="File too large (max 12MB)")
    filename = file.filename or ""
    if modality == "audio":
        return assess_audio_bytes(data=data, filename=filename, lang=lang, user_id=user_id, persist=persist)
    return assess_media_bytes(data=data, filename=filename, lang=lang, user_id=user_id, persist=persist)


@router.get("/assessments/{assessment_id}", response_model=TrustAssessmentOut)
def api_get_trust_assessment(assessment_id: int):
    row = get_trust_assessment(assessment_id)
    if not row:
        raise HTTPException(status_code=404, detail="Trust assessment not found")
    legacy = row.pop("payload", {})
    return {
        "id": row["id"],
        "object_type": row["object_type"],
        "object_id": row["object_id"],
        "score": row["score"],
        "band": row["band"],
        "certainty": row["certainty"],
        "signals": row["signals"],
        "evidence_refs": row["evidence_refs"],
        "verification_check_id": row["verification_check_id"],
        "legacy": legacy,
        "honesty_note": (
            "Trust assessments are explainable decision support. "
            "They never claim absolute certainty."
        ),
    }
