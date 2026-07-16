"""MboaShield application factory."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import api_router
from .core.config import ROOT, VERSION, get_settings
from .core.errors import AppError, app_error_handler, http_exception_handler
from .core.middleware import RateLimitMiddleware, RequestContextMiddleware
from .db.session import init_db
from .repositories import list_institutions
from .seed import seed_institutions_if_needed

FRONTEND = ROOT / "frontend"


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="MboaShield API",
        version=settings.version,
        description=(
            "National Digital Trust Platform — Made in Cameroon by Justene Nkwagoh Tamah. "
            "Detection, explanation, escalation, and civic recovery."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins != ["*"] else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RateLimitMiddleware)
    application.add_middleware(RequestContextMiddleware)

    application.add_exception_handler(AppError, app_error_handler)
    application.add_exception_handler(HTTPException, http_exception_handler)

    init_db()
    seed_institutions_if_needed()

    @application.get("/health")
    def health():
        institutions = list_institutions()
        db_url = settings.resolved_database_url()
        dialect = "postgresql" if db_url.startswith("postgresql") else "sqlite"
        return {
            "status": "ok",
            "version": settings.version,
            "founder": "Justene Nkwagoh Tamah",
            "product": "MboaShield",
            "environment": settings.environment,
            "database": dialect,
            "auth_enforce": settings.auth_enforce,
            "institutions_count": len(institutions),
            "ai_engine": "mboashield-trust-engine",
            "ai_engine_version": "0.6.0",
            "nlp_engine": "mboashield-text-nlp-v1",
            "media_adapter": "mboashield-media-adapter-v1",
            "audio_adapter": "mboashield-audio-adapter-v1",
        }

    application.include_router(api_router)

    @application.get("/")
    def index():
        index_path = FRONTEND / "index.html"
        if not index_path.exists():
            raise HTTPException(status_code=404, detail="Frontend missing")
        return FileResponse(index_path)

    if FRONTEND.exists():
        application.mount("/static", StaticFiles(directory=FRONTEND / "static"), name="static")

    return application


app = create_app()

# Backward-compatible re-export
__all__ = ["app", "create_app", "VERSION"]
