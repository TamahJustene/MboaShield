from __future__ import annotations

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import DB_PATH, ROOT, VERSION
from .db import init_db
from .repositories import (
    create_user,
    get_certificate,
    get_institution,
    get_user,
    get_verification_check,
    list_institutions,
    list_recent_certificates,
    list_recent_verification_checks,
    save_certificate,
    save_verification_check,
)
from .schemas import (
    CertificateOut,
    CompleteIn,
    ImpersonationIn,
    InstitutionOut,
    InstitutionsOut,
    RecentCertificatesOut,
    RecentChecksOut,
    StoredCheckOut,
    TextIn,
    UserIn,
    UserOut,
)
from .seed import seed_institutions_if_needed
from .services import ambassadors, audio_check, impersonation, media_check, source_verify, text_check

FRONTEND = ROOT / "frontend"

app = FastAPI(
    title="MboaShield API",
    version=VERSION,
    description="Sovereign AI shield MVP - Made in Cameroon by Justene Nkwagoh Tamah",
)

init_db()
seed_institutions_if_needed()


def resolve_user_id(x_mboashield_user_id: str | None = Header(default=None)) -> int | None:
    if not x_mboashield_user_id:
        return None
    try:
        user_id = int(x_mboashield_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid X-MboaShield-User-Id header") from exc
    if not get_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return user_id


@app.get("/health")
def health():
    institutions = list_institutions()
    return {
        "status": "ok",
        "version": VERSION,
        "founder": "Justene Nkwagoh Tamah",
        "product": "MboaShield",
        "db_path": str(DB_PATH),
        "institutions_count": len(institutions),
    }


@app.post("/api/v1/users", response_model=UserOut)
def api_create_user(body: UserIn):
    try:
        return create_user(display_name=body.display_name, email=body.email)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/users/{user_id}", response_model=UserOut)
def api_get_user(user_id: int):
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/api/v1/institutions", response_model=InstitutionsOut)
def api_list_institutions():
    institutions = list_institutions()
    return {"institutions": institutions, "count": len(institutions)}


@app.get("/api/v1/institutions/{institution_id}", response_model=InstitutionOut)
def api_get_institution(institution_id: str):
    institution = get_institution(institution_id)
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    return institution


@app.post("/api/v1/check/text")
def api_check_text(
    body: TextIn,
    x_mboashield_user_id: str | None = Header(default=None),
):
    resolved_user_id = resolve_user_id(x_mboashield_user_id)
    result = text_check.check_text(body.text, body.lang).as_dict()
    result["source_verification"] = source_verify.verify_claim(body.text, body.lang).as_dict()
    result["check_id"] = save_verification_check(
        check_type="text",
        result=result,
        lang=body.lang,
        input_text=body.text,
        user_id=resolved_user_id,
    )
    return result


@app.post("/api/v1/check/impersonation")
def api_check_impersonation(
    body: ImpersonationIn,
    x_mboashield_user_id: str | None = Header(default=None),
):
    resolved_user_id = resolve_user_id(x_mboashield_user_id)
    result = impersonation.check_impersonation(body.name, body.handle, body.lang).as_dict()
    result["check_id"] = save_verification_check(
        check_type="impersonation",
        result=result,
        lang=body.lang,
        input_text=body.name,
        input_handle=body.handle,
        user_id=resolved_user_id,
    )
    return result


@app.post("/api/v1/check/media")
async def api_check_media(
    file: UploadFile = File(...),
    lang: str = Form("en"),
    x_mboashield_user_id: str | None = Header(default=None),
):
    resolved_user_id = resolve_user_id(x_mboashield_user_id)
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > 8_000_000:
        raise HTTPException(status_code=400, detail="File too large (max 8MB)")
    result = media_check.check_image_bytes(data, file.filename or "", lang).as_dict()
    result["check_id"] = save_verification_check(
        check_type="media",
        result=result,
        lang=lang,
        input_filename=file.filename or "",
        user_id=resolved_user_id,
    )
    return result


@app.post("/api/v1/check/audio")
async def api_check_audio(
    file: UploadFile = File(...),
    lang: str = Form("en"),
    x_mboashield_user_id: str | None = Header(default=None),
):
    resolved_user_id = resolve_user_id(x_mboashield_user_id)
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > 12_000_000:
        raise HTTPException(status_code=400, detail="File too large (max 12MB)")
    result = audio_check.check_audio_bytes(data, file.filename or "", lang).as_dict()
    result["check_id"] = save_verification_check(
        check_type="audio",
        result=result,
        lang=lang,
        input_filename=file.filename or "",
        user_id=resolved_user_id,
    )
    return result


@app.get("/api/v1/checks/recent", response_model=RecentChecksOut)
def api_recent_checks(limit: int = 20, check_type: str | None = None):
    checks = list_recent_verification_checks(limit=limit, check_type=check_type)
    return {"checks": checks, "count": len(checks)}


@app.get("/api/v1/checks/{check_id}", response_model=StoredCheckOut)
def api_get_check(check_id: int):
    check = get_verification_check(check_id)
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
    return check


@app.get("/api/v1/certificates/recent", response_model=RecentCertificatesOut)
def api_recent_certificates(limit: int = 20):
    certificates = list_recent_certificates(limit=limit)
    return {"certificates": certificates, "count": len(certificates)}


@app.get("/api/v1/certificates/{certificate_id}", response_model=CertificateOut)
def api_get_certificate(certificate_id: str):
    certificate = get_certificate(certificate_id)
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return certificate


@app.get("/api/v1/ambassadors/lessons")
def api_lessons():
    return {"lessons": ambassadors.list_lessons()}


@app.post("/api/v1/ambassadors/complete")
def api_complete(body: CompleteIn):
    result = ambassadors.complete_lesson(body.lesson_id, body.learner_name)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error", "Not found"))
    save_certificate(result["certificate"])
    return result


@app.get("/")
def index():
    index_path = FRONTEND / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend missing")
    return FileResponse(index_path)


if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND / "static"), name="static")
