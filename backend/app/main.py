"""MboaShield application factory."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .api import api_router
from .api.public_verify import router as public_verify_router
from .api.v1.scim import router as scim_router
from .ai_store import ensure_builtin_models
from .governance_store import ensure_governance_seed
from .core.config import ROOT, VERSION, get_settings
from .core.errors import AppError, app_error_handler, http_exception_handler
from .core.metrics import MetricsMiddleware, metrics_payload, refresh_app_info
from .core.middleware import RateLimitMiddleware, RequestContextMiddleware
from .core.security import oidc_providers, production_security_warnings
from .db.session import init_db
from .identity_store import ensure_default_tenant
from .repositories import list_institutions
from .seed import seed_institutions_if_needed
from .services.ai_analysis import ENGINE_VERSION as AI_ENGINE_VERSION
from .core.openapi_pillars import OPENAPI_TAGS, PROGRAM_ID, TRANSFORMATION_PHASE
from .workers.enqueue import workers_active

FRONTEND = ROOT / "frontend"


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="MboaShield Trust API",
        version=settings.version,
        openapi_tags=OPENAPI_TAGS,
        description=(
            "MboaShield National Digital Trust Infrastructure (2030 program). "
            "National platforms exposed as versioned REST APIs. "
            "Made in Cameroon by Justene Nkwagoh Tamah. "
            "Detection, explanation, investigation, and interoperable trust services."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    def _custom_openapi():
        if application.openapi_schema:
            return application.openapi_schema
        from fastapi.openapi.utils import get_openapi

        schema = get_openapi(
            title=application.title,
            version=application.version,
            description=application.description,
            routes=application.routes,
            tags=OPENAPI_TAGS,
        )
        schema.setdefault("info", {})["x-mboashield-program"] = PROGRAM_ID
        schema["info"]["x-transformation-phase"] = TRANSFORMATION_PHASE
        application.openapi_schema = schema
        return application.openapi_schema

    application.openapi = _custom_openapi  # type: ignore[method-assign]

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
    if settings.metrics_enabled:
        application.add_middleware(MetricsMiddleware)
        refresh_app_info()

    application.add_exception_handler(AppError, app_error_handler)
    application.add_exception_handler(HTTPException, http_exception_handler)

    init_db()
    seed_institutions_if_needed()
    ensure_default_tenant()
    if settings.advanced_ai_enabled:
        ensure_builtin_models()
    if settings.governance_enabled:
        ensure_governance_seed()

    @application.get("/health")
    def health():
        institutions = list_institutions()
        db_url = settings.resolved_database_url()
        dialect = "postgresql" if db_url.startswith("postgresql") else "sqlite"
        return {
            "status": "ok",
            "version": settings.version,
            "program": PROGRAM_ID,
            "transformation_phase": TRANSFORMATION_PHASE,
            "country_pack": settings.country_pack,
            "tenant_id": settings.tenant_id,
            "founder": "Justene Nkwagoh Tamah",
            "product": "MboaShield",
            "environment": settings.environment,
            "database": dialect,
            "auth_enforce": settings.auth_enforce,
            "institutions_count": len(institutions),
            "ai_engine": "mboashield-trust-engine",
            "ai_engine_version": AI_ENGINE_VERSION,
            "intelligence_engines": 10,
            "analytics": "national-v1",
            "deployment_profile": settings.deployment_profile,
            "ntoc": settings.ntoc_enabled,
            "intel": settings.intel_enabled,
            "vault": settings.vault_enabled,
            "institution_portal": settings.institution_portal_enabled,
            "verified_comms": settings.verified_comms_enabled,
            "advanced_ai": settings.advanced_ai_enabled,
            "metrics": settings.metrics_enabled,
            "workers": workers_active(),
            "governance": settings.governance_enabled,
            "scim_read_only": True,
            "identity": {
                "mfa_ready": True,
                "oidc_ready": bool(
                    settings.oidc_enabled
                    and settings.oidc_issuer
                    and settings.oidc_client_id
                    and settings.oidc_client_secret
                ),
                "oidc_providers": len(oidc_providers()),
                "saml_ready": bool(settings.saml_enabled),
                "ldap_ready": bool(settings.ldap_enabled and settings.ldap_server_uri),
                "partner_api_keys": True,
                "oauth2_client_credentials": True,
                "sessions": True,
                "trusted_devices": True,
                "admin_users": True,
                "security_warnings": production_security_warnings(),
            },
            "nlp_engine": "mboashield-text-nlp-v1",
            "media_adapter": "mboashield-media-adapter-v1",
            "audio_adapter": "mboashield-audio-adapter-v1",
        }

    @application.get("/metrics")
    def metrics():
        if not settings.metrics_enabled:
            raise HTTPException(status_code=404, detail="Metrics disabled")
        body, content_type = metrics_payload()
        return Response(content=body, media_type=content_type)

    application.include_router(api_router)
    application.include_router(public_verify_router)
    application.include_router(scim_router)

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
