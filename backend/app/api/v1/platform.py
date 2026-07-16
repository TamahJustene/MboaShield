"""Existing v1 platform routes - preserved contracts under /api/v1/*."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from ...repositories import (
    create_incident_report,
    create_user,
    get_certificate,
    get_incident_report,
    get_institution,
    get_user,
    get_verification_check,
    list_audit_logs,
    list_incident_reports,
    list_institutions,
    list_recent_certificates,
    list_recent_verification_checks,
    save_certificate,
    save_verification_check,
    update_incident_status,
    write_audit_log,
)
from ...schemas import (
    CaseAnalyzeIn,
    CertificateOut,
    CompleteIn,
    ImpersonationIn,
    IncidentReportIn,
    IncidentReportOut,
    IncidentReportsOut,
    IncidentStatusIn,
    InstitutionOut,
    InstitutionsOut,
    RecentCertificatesOut,
    RecentChecksOut,
    StoredCheckOut,
    TextIn,
    UserIn,
    UserOut,
)
from ...services import ambassadors, impersonation, source_verify, text_check
from ...services.ai_analysis import analyze_case, enrich_result
from ...services.model_adapters import analyze_audio_with_fallback, analyze_image_with_fallback
from ..deps import LegacyUserId, require_permission

router = APIRouter(tags=["platform"])


@router.post("/users", response_model=UserOut)
def api_create_user(body: UserIn):
    try:
        return create_user(display_name=body.display_name, email=body.email)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/users/{user_id}", response_model=UserOut)
def api_get_user(user_id: int):
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/institutions", response_model=InstitutionsOut)
def api_list_institutions():
    institutions = list_institutions()
    return {"institutions": institutions, "count": len(institutions)}


@router.get("/institutions/{institution_id}", response_model=InstitutionOut)
def api_get_institution(institution_id: str):
    institution = get_institution(institution_id)
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    return institution


@router.post("/incidents", response_model=IncidentReportOut)
def api_create_incident(body: IncidentReportIn, user_id: LegacyUserId):
    try:
        return create_incident_report(
            report_type=body.report_type,
            description=body.description,
            verification_check_id=body.verification_check_id,
            user_id=user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/incidents", response_model=IncidentReportsOut)
def api_list_incidents(limit: int = 20, status: str | None = None):
    try:
        reports = list_incident_reports(limit=limit, status=status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"reports": reports, "count": len(reports)}


@router.get("/incidents/{report_id}", response_model=IncidentReportOut)
def api_get_incident(report_id: int):
    report = get_incident_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Incident report not found")
    return report


@router.patch("/incidents/{report_id}", response_model=IncidentReportOut)
def api_update_incident(
    report_id: int,
    body: IncidentStatusIn,
    request: Request,
    _actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    try:
        report = update_incident_status(
            report_id,
            status=body.status,
            reviewer_note=body.reviewer_note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not report:
        raise HTTPException(status_code=404, detail="Incident report not found")

    actor = getattr(request.state, "actor", None) or _actor
    write_audit_log(
        action="incident.status_update",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="incident",
        resource_id=str(report_id),
        details={"status": body.status},
        ip_address=request.client.host if request.client else None,
    )
    return report


@router.post("/check/text")
def api_check_text(body: TextIn, user_id: LegacyUserId):
    result = text_check.check_text(body.text, body.lang).as_dict()
    result["source_verification"] = source_verify.verify_claim(body.text, body.lang).as_dict()
    result = enrich_result(result, modality="text", lang=body.lang)
    result["check_id"] = save_verification_check(
        check_type="text",
        result=result,
        lang=body.lang,
        input_text=body.text,
        user_id=user_id,
    )
    return result


@router.post("/check/impersonation")
def api_check_impersonation(body: ImpersonationIn, user_id: LegacyUserId):
    result = impersonation.check_impersonation(body.name, body.handle, body.lang).as_dict()
    result = enrich_result(result, modality="impersonation", lang=body.lang)
    result["check_id"] = save_verification_check(
        check_type="impersonation",
        result=result,
        lang=body.lang,
        input_text=body.name,
        input_handle=body.handle,
        user_id=user_id,
    )
    return result


@router.post("/check/media")
async def api_check_media(
    user_id: LegacyUserId,
    file: UploadFile = File(...),
    lang: str = Form("en"),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > 8_000_000:
        raise HTTPException(status_code=400, detail="File too large (max 8MB)")
    result = analyze_image_with_fallback(data, file.filename or "", lang)
    result = enrich_result(result, modality="media", lang=lang)
    result["check_id"] = save_verification_check(
        check_type="media",
        result=result,
        lang=lang,
        input_filename=file.filename or "",
        user_id=user_id,
    )
    return result


@router.post("/check/audio")
async def api_check_audio(
    user_id: LegacyUserId,
    file: UploadFile = File(...),
    lang: str = Form("en"),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > 12_000_000:
        raise HTTPException(status_code=400, detail="File too large (max 12MB)")
    result = analyze_audio_with_fallback(data, file.filename or "", lang)
    result = enrich_result(result, modality="audio", lang=lang)
    result["check_id"] = save_verification_check(
        check_type="audio",
        result=result,
        lang=lang,
        input_filename=file.filename or "",
        user_id=user_id,
    )
    return result


@router.post("/analyze")
def api_analyze_case(body: CaseAnalyzeIn, user_id: LegacyUserId):
    if not body.text.strip() and not body.name.strip() and not body.handle.strip():
        raise HTTPException(status_code=400, detail="Provide text and/or account identity fields")

    case = analyze_case(text=body.text, name=body.name, handle=body.handle, lang=body.lang)

    check_id = None
    for module in case.get("modules", []):
        modality = module["modality"]
        result = module["result"]
        if modality == "text":
            check_id = save_verification_check(
                check_type="text",
                result=result,
                lang=body.lang,
                input_text=body.text,
                user_id=user_id,
            )
            result["check_id"] = check_id
        elif modality == "impersonation":
            saved = save_verification_check(
                check_type="impersonation",
                result=result,
                lang=body.lang,
                input_text=body.name,
                input_handle=body.handle,
                user_id=user_id,
            )
            result["check_id"] = saved
            if check_id is None:
                check_id = saved

    case["case_check_id"] = check_id
    return case


@router.get("/checks/recent", response_model=RecentChecksOut)
def api_recent_checks(limit: int = 20, check_type: str | None = None):
    checks = list_recent_verification_checks(limit=limit, check_type=check_type)
    return {"checks": checks, "count": len(checks)}


@router.get("/checks/{check_id}", response_model=StoredCheckOut)
def api_get_check(check_id: int):
    check = get_verification_check(check_id)
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
    return check


@router.get("/certificates/recent", response_model=RecentCertificatesOut)
def api_recent_certificates(limit: int = 20):
    certificates = list_recent_certificates(limit=limit)
    return {"certificates": certificates, "count": len(certificates)}


@router.get("/certificates/{certificate_id}", response_model=CertificateOut)
def api_get_certificate(certificate_id: str):
    certificate = get_certificate(certificate_id)
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return certificate


@router.get("/ambassadors/lessons")
def api_lessons():
    return {"lessons": ambassadors.list_lessons()}


@router.post("/ambassadors/complete")
def api_complete(body: CompleteIn):
    result = ambassadors.complete_lesson(body.lesson_id, body.learner_name)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error", "Not found"))
    save_certificate(result["certificate"])
    return result


@router.get("/audit/logs")
def api_audit_logs(
    limit: int = 50,
    _actor: Annotated[dict | None, Depends(require_permission("audit:read"))] = None,
):
    logs = list_audit_logs(limit=limit)
    return {"logs": logs, "count": len(logs)}
