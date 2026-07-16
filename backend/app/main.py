from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import ROOT, VERSION
from .services import ambassadors, audio_check, impersonation, media_check, source_verify, text_check

FRONTEND = ROOT / "frontend"

app = FastAPI(
    title="MboaShield API",
    version=VERSION,
    description="Sovereign AI shield MVP - Made in Cameroon by Justene Nkwagoh Tamah",
)


class TextIn(BaseModel):
    text: str = Field(..., min_length=1)
    lang: str = "en"


class ImpersonationIn(BaseModel):
    name: str = ""
    handle: str = ""
    lang: str = "en"


class CompleteIn(BaseModel):
    lesson_id: str
    learner_name: str = "Citizen"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": VERSION,
        "founder": "Justene Nkwagoh Tamah",
        "product": "MboaShield",
    }


@app.post("/api/v1/check/text")
def api_check_text(body: TextIn):
    result = text_check.check_text(body.text, body.lang).as_dict()
    result["source_verification"] = source_verify.verify_claim(body.text, body.lang).as_dict()
    return result


@app.post("/api/v1/check/impersonation")
def api_check_impersonation(body: ImpersonationIn):
    return impersonation.check_impersonation(body.name, body.handle, body.lang).as_dict()


@app.post("/api/v1/check/media")
async def api_check_media(
    file: UploadFile = File(...),
    lang: str = Form("en"),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > 8_000_000:
        raise HTTPException(status_code=400, detail="File too large (max 8MB)")
    return media_check.check_image_bytes(data, file.filename or "", lang).as_dict()


@app.post("/api/v1/check/audio")
async def api_check_audio(
    file: UploadFile = File(...),
    lang: str = Form("en"),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > 12_000_000:
        raise HTTPException(status_code=400, detail="File too large (max 12MB)")
    return audio_check.check_audio_bytes(data, file.filename or "", lang).as_dict()


@app.get("/api/v1/ambassadors/lessons")
def api_lessons():
    return {"lessons": ambassadors.list_lessons()}


@app.post("/api/v1/ambassadors/complete")
def api_complete(body: CompleteIn):
    result = ambassadors.complete_lesson(body.lesson_id, body.learner_name)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error", "Not found"))
    return result


@app.get("/")
def index():
    index_path = FRONTEND / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend missing")
    return FileResponse(index_path)


if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND / "static"), name="static")
