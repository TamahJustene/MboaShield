"""Zero-trust checklist helpers (T5)."""

from __future__ import annotations

from typing import Any

from .config import get_settings
from .security import DEFAULT_JWT_SECRET, production_security_warnings


def zero_trust_checklist() -> dict[str, Any]:
    settings = get_settings()
    auth_ok = bool(settings.auth_enforce)
    jwt_ok = settings.jwt_secret != DEFAULT_JWT_SECRET
    cors_ok = settings.cors_origins.strip() != "*"
    mfa_ok = bool(settings.mfa_enforce) or bool(settings.mfa_roles())
    warnings = production_security_warnings()
    checks = {
        "auth_enforce": auth_ok,
        "national_or_government_profile": settings.is_government_profile(),
        "jwt_secret_rotated": jwt_ok,
        "cors_locked": cors_ok,
        "mfa_policy_present": mfa_ok,
        "scim_read_available": True,
        "rls_sql_template_shipped": True,
        "kms_guide_shipped": True,
    }
    score = sum(1 for value in checks.values() if value)
    return {
        "national_default_profile": "deploy/profiles/national.env",
        "recommended_auth_enforce": True,
        "current_auth_enforce": settings.auth_enforce,
        "deployment_profile": settings.deployment_profile,
        "checks": checks,
        "score": score,
        "max_score": len(checks),
        "ready_for_national": auth_ok and jwt_ok and len(warnings) == 0,
        "warnings": warnings,
        "docs": {
            "kms": "docs/manuals/KMS_AND_SECRETS.md",
            "rls": "deploy/sql/rls_tenant.sql",
            "adr": "docs/adr/0006-zero-trust-national-identity.md",
        },
    }
