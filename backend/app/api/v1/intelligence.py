"""Modular intelligence engine API."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ...schemas import IntelligenceAnalyzeIn
from ...services.engines import analyze_intelligence, list_engines

router = APIRouter(prefix="/intelligence", tags=["pillar-trust"])


@router.get("/engines")
def api_list_engines():
    engines = list_engines()
    return {
        "engines": engines,
        "count": len(engines),
        "contract": [
            "confidence",
            "evidence",
            "reasoning",
            "risk_level",
            "threat_category",
            "recommendations",
        ],
        "honesty_note": "Engines provide explainable signals and never claim certainty.",
    }


@router.post("/analyze")
def api_intelligence_analyze(body: IntelligenceAnalyzeIn):
    if not any(
        [
            body.text.strip(),
            body.name.strip(),
            body.handle.strip(),
            body.url.strip(),
            body.filename.strip(),
        ]
    ):
        raise HTTPException(status_code=400, detail="Provide text, identity, URL, or filename context")
    return analyze_intelligence(
        text=body.text,
        name=body.name,
        handle=body.handle,
        url=body.url,
        filename=body.filename,
        mime_type=body.mime_type,
        lang=body.lang,
        include_scaffolds=body.include_scaffolds,
    )


@router.post("/analyze/media")
async def api_intelligence_analyze_media(
    file: UploadFile = File(...),
    lang: str = Form("en"),
    modality: str = Form("image"),
    text: str = Form(""),
    name: str = Form(""),
    handle: str = Form(""),
    include_scaffolds: bool = Form(True),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > 12_000_000:
        raise HTTPException(status_code=400, detail="File too large (max 12MB)")

    image_bytes = data if modality == "image" else None
    audio_bytes = data if modality == "audio" else None
    return analyze_intelligence(
        text=text,
        name=name,
        handle=handle,
        filename=file.filename or "",
        mime_type=file.content_type or "",
        size_bytes=len(data),
        image_bytes=image_bytes,
        audio_bytes=audio_bytes,
        lang=lang,
        include_scaffolds=include_scaffolds,
    )
