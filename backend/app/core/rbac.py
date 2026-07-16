from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    CITIZEN = "citizen"
    ANALYST = "analyst"
    INSTITUTION_ADMIN = "institution_admin"
    ADMIN = "admin"


ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.CITIZEN: {
        "checks:create",
        "incidents:create",
        "history:read_own",
        "ambassadors:complete",
        "institutions:read",
    },
    Role.ANALYST: {
        "checks:create",
        "incidents:create",
        "incidents:review",
        "history:read_all",
        "ambassadors:complete",
        "institutions:read",
        "audit:read",
    },
    Role.INSTITUTION_ADMIN: {
        "checks:create",
        "incidents:create",
        "incidents:review",
        "history:read_all",
        "institutions:read",
        "institutions:manage",
    },
    Role.ADMIN: {
        "checks:create",
        "incidents:create",
        "incidents:review",
        "history:read_all",
        "ambassadors:complete",
        "institutions:read",
        "institutions:manage",
        "audit:read",
        "users:manage",
        "partners:manage",
        "system:admin",
    },
}


def has_permission(role: str | Role, permission: str) -> bool:
    try:
        role_enum = Role(role)
    except ValueError:
        return False
    return permission in ROLE_PERMISSIONS.get(role_enum, set())
