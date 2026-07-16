"""Institution Administration Platform (Phase 10)."""

from __future__ import annotations

import json
import re
import secrets
from typing import Any

from sqlalchemy import func, select

from .core.config import get_settings
from .core.security import generate_institution_api_key, hash_api_key
from .db.models import (
    IncidentReport,
    Institution,
    InstitutionApiKey,
    InstitutionDomain,
    InstitutionMembership,
    InstitutionOfficialAccount,
    InvestigationCase,
    User,
)
from .db.session import session_scope
from .repositories import get_institution, get_user, now_iso

DOMAIN_RE = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$", re.I)
ALLOWED_MEMBER_ROLES = {"member", "admin"}
ALLOWED_MEMBER_STATUS = {"active", "invited", "disabled"}
DEFAULT_INSTITUTION_SCOPES = ["checks:create", "institutions:read", "incidents:create"]


def _tokens_match(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    import hashlib
    import hmac

    return hmac.compare_digest(
        hashlib.sha256(left.encode("utf-8")).digest(),
        hashlib.sha256(right.encode("utf-8")).digest(),
    )


def _domain_to_dict(row: InstitutionDomain) -> dict[str, Any]:
    return {
        "id": row.id,
        "institution_id": row.institution_id,
        "domain": row.domain,
        "verification_token": row.verification_token,
        "verification_method": row.verification_method,
        "verified": bool(row.verified),
        "verified_at": row.verified_at,
        "dns_txt_name": f"_mboashield.{row.domain}",
        "dns_txt_value": f"mboashield-verify={row.verification_token}",
        "created_by_user_id": row.created_by_user_id,
        "created_at": row.created_at,
    }


def _membership_to_dict(row: InstitutionMembership, user: User | None = None) -> dict[str, Any]:
    payload = {
        "id": row.id,
        "institution_id": row.institution_id,
        "user_id": row.user_id,
        "member_role": row.member_role,
        "status": row.status,
        "invited_by_user_id": row.invited_by_user_id,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }
    if user is not None:
        payload["user"] = {
            "id": user.id,
            "display_name": user.display_name,
            "email": user.email,
            "role": user.role,
        }
    return payload


def _account_to_dict(row: InstitutionOfficialAccount) -> dict[str, Any]:
    return {
        "id": row.id,
        "institution_id": row.institution_id,
        "platform": row.platform,
        "handle": row.handle,
        "url": row.url,
        "verified": bool(row.verified),
        "created_at": row.created_at,
    }


def _api_key_to_dict(row: InstitutionApiKey, *, include_raw: str | None = None) -> dict[str, Any]:
    payload = {
        "id": row.id,
        "institution_id": row.institution_id,
        "name": row.name,
        "key_prefix": row.key_prefix,
        "scopes": json.loads(row.scopes_json or "[]"),
        "created_by_user_id": row.created_by_user_id,
        "revoked": bool(row.revoked),
        "expires_at": row.expires_at,
        "last_used_at": row.last_used_at,
        "created_at": row.created_at,
    }
    if include_raw:
        payload["api_key"] = include_raw
    return payload


def normalize_domain(domain: str) -> str:
    value = (domain or "").strip().lower()
    value = value.removeprefix("https://").removeprefix("http://")
    value = value.split("/")[0].split(":")[0]
    if value.startswith("www."):
        value = value[4:]
    if not value or not DOMAIN_RE.match(value):
        raise ValueError("Invalid domain")
    return value


def actor_is_platform_admin(actor: dict | None) -> bool:
    return bool(actor and actor.get("role") == "admin")


def get_membership(institution_id: str, user_id: int) -> dict[str, Any] | None:
    with session_scope() as session:
        row = session.execute(
            select(InstitutionMembership).where(
                InstitutionMembership.institution_id == institution_id,
                InstitutionMembership.user_id == user_id,
            )
        ).scalar_one_or_none()
        return _membership_to_dict(row) if row else None


def assert_institution_portal_access(
    actor: dict | None,
    institution_id: str,
    *,
    require_admin: bool = False,
) -> None:
    """Enforce membership when AUTH_ENFORCE=true; soft mode skips."""
    settings = get_settings()
    if not settings.auth_enforce:
        return
    if not actor:
        raise PermissionError("Authentication required")
    if actor.get("auth_type") == "api_key" and actor.get("institution_id") == institution_id:
        if require_admin and "institutions:manage" not in (actor.get("scopes") or []):
            raise PermissionError("Institution admin scope required")
        return
    if actor_is_platform_admin(actor):
        return
    user_id = actor.get("id")
    if not user_id:
        raise PermissionError("User identity required")
    membership = get_membership(institution_id, int(user_id))
    if not membership or membership.get("status") != "active":
        raise PermissionError("Not a member of this institution")
    if require_admin and membership.get("member_role") != "admin":
        raise PermissionError("Institution admin membership required")


def portal_overview(institution_id: str) -> dict[str, Any]:
    institution = get_institution(institution_id)
    if not institution:
        raise ValueError("Institution not found")
    domains = list_domains(institution_id)
    memberships = list_memberships(institution_id)
    accounts = list_official_accounts(institution_id)
    keys = list_api_keys(institution_id)
    analytics = institution_analytics(institution_id)
    return {
        "institution": institution,
        "domains": domains,
        "memberships": memberships,
        "official_accounts": accounts,
        "api_keys": keys,
        "analytics": analytics,
        "verified_domains": sum(1 for item in domains if item.get("verified")),
        "active_members": sum(1 for item in memberships if item.get("status") == "active"),
    }


def list_domains(institution_id: str) -> list[dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(
            select(InstitutionDomain)
            .where(InstitutionDomain.institution_id == institution_id)
            .order_by(InstitutionDomain.id.desc())
        ).scalars().all()
        return [_domain_to_dict(row) for row in rows]


def add_domain(
    institution_id: str,
    domain: str,
    *,
    verification_method: str = "dns_txt",
    created_by_user_id: int | None = None,
) -> dict[str, Any]:
    if not get_institution(institution_id):
        raise ValueError("Institution not found")
    normalized = normalize_domain(domain)
    method = (verification_method or "dns_txt").strip().lower()
    if method not in {"dns_txt", "token_confirm", "http_file"}:
        raise ValueError("verification_method must be dns_txt, token_confirm, or http_file")
    token = secrets.token_urlsafe(24)
    with session_scope() as session:
        existing = session.execute(
            select(InstitutionDomain).where(
                InstitutionDomain.institution_id == institution_id,
                InstitutionDomain.domain == normalized,
            )
        ).scalar_one_or_none()
        if existing:
            raise ValueError("Domain already registered for this institution")
        row = InstitutionDomain(
            institution_id=institution_id,
            domain=normalized,
            verification_token=token,
            verification_method=method,
            verified=False,
            verified_at=None,
            created_by_user_id=created_by_user_id,
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        return _domain_to_dict(row)


def verify_domain(
    institution_id: str,
    domain_id: int,
    *,
    provided_token: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    with session_scope() as session:
        row = session.get(InstitutionDomain, domain_id)
        if not row or row.institution_id != institution_id:
            raise ValueError("Domain not found")
        if row.verified:
            return _domain_to_dict(row)

        ok = False
        if force and get_settings().deployment_profile.strip().lower() == "demo":
            ok = True
        elif row.verification_method == "token_confirm":
            ok = _tokens_match(provided_token, row.verification_token)
        elif row.verification_method == "dns_txt":
            ok = _check_dns_txt(row.domain, row.verification_token)
            if not ok and _tokens_match(provided_token, row.verification_token):
                # Allow explicit token confirm as operator fallback when DNS not ready
                ok = True
        elif row.verification_method == "http_file":
            if _tokens_match(provided_token, row.verification_token):
                ok = True

        if not ok:
            raise ValueError("Domain verification failed")
        row.verified = True
        row.verified_at = now_iso()
        session.flush()
        return _domain_to_dict(row)


def _check_dns_txt(domain: str, token: str) -> bool:
    try:
        import dns.resolver  # type: ignore
    except ImportError:
        return False
    name = f"_mboashield.{domain}"
    expected = f"mboashield-verify={token}"
    try:
        answers = dns.resolver.resolve(name, "TXT")
        for answer in answers:
            for text in getattr(answer, "strings", []) or []:
                value = text.decode("utf-8") if isinstance(text, bytes) else str(text)
                if expected in value.replace('"', ""):
                    return True
    except Exception:
        return False
    return False


def list_memberships(institution_id: str) -> list[dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(
            select(InstitutionMembership, User)
            .join(User, User.id == InstitutionMembership.user_id)
            .where(InstitutionMembership.institution_id == institution_id)
            .order_by(InstitutionMembership.id.desc())
        ).all()
        return [_membership_to_dict(membership, user) for membership, user in rows]


def add_membership(
    institution_id: str,
    *,
    user_id: int | None = None,
    email: str | None = None,
    display_name: str | None = None,
    member_role: str = "member",
    invited_by_user_id: int | None = None,
) -> dict[str, Any]:
    if not get_institution(institution_id):
        raise ValueError("Institution not found")
    role = (member_role or "member").strip().lower()
    if role not in ALLOWED_MEMBER_ROLES:
        raise ValueError("member_role must be member or admin")

    target_user_id = user_id
    created_user: dict | None = None
    if target_user_id is None:
        email_norm = (email or "").strip().lower()
        if not email_norm:
            raise ValueError("user_id or email is required")
        with session_scope() as session:
            existing = session.execute(select(User).where(User.email == email_norm)).scalar_one_or_none()
            if existing:
                target_user_id = existing.id
            else:
                from .identity_store import admin_create_user

                created_user = admin_create_user(
                    display_name=display_name or email_norm.split("@")[0],
                    email=email_norm,
                    role="institution_admin" if role == "admin" else "citizen",
                    password=None,
                    invited_by_user_id=invited_by_user_id,
                    must_reset_password=True,
                )
                target_user_id = created_user["id"]

    if not get_user(int(target_user_id)):
        raise ValueError("User not found")

    now = now_iso()
    with session_scope() as session:
        existing = session.execute(
            select(InstitutionMembership).where(
                InstitutionMembership.institution_id == institution_id,
                InstitutionMembership.user_id == target_user_id,
            )
        ).scalar_one_or_none()
        if existing:
            raise ValueError("User is already a member")
        row = InstitutionMembership(
            institution_id=institution_id,
            user_id=int(target_user_id),
            member_role=role,
            status="active",
            invited_by_user_id=invited_by_user_id,
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        session.flush()
        user = session.get(User, int(target_user_id))
        payload = _membership_to_dict(row, user)
        if created_user and created_user.get("temporary_password"):
            payload["temporary_password"] = created_user["temporary_password"]
        return payload


def update_membership(
    institution_id: str,
    membership_id: int,
    *,
    member_role: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    with session_scope() as session:
        row = session.get(InstitutionMembership, membership_id)
        if not row or row.institution_id != institution_id:
            raise ValueError("Membership not found")
        if member_role is not None:
            role = member_role.strip().lower()
            if role not in ALLOWED_MEMBER_ROLES:
                raise ValueError("member_role must be member or admin")
            row.member_role = role
        if status is not None:
            st = status.strip().lower()
            if st not in ALLOWED_MEMBER_STATUS:
                raise ValueError("Invalid membership status")
            row.status = st
        row.updated_at = now_iso()
        session.flush()
        user = session.get(User, row.user_id)
        return _membership_to_dict(row, user)


def get_branding(institution_id: str) -> dict[str, Any]:
    institution = get_institution(institution_id)
    if not institution:
        raise ValueError("Institution not found")
    return {
        "institution_id": institution_id,
        "branding": institution.get("branding") or {},
        "contact_email": institution.get("contact_email"),
        "name": institution.get("name"),
        "short_name": institution.get("short_name"),
        "url": institution.get("url"),
    }


def update_branding(
    institution_id: str,
    *,
    branding: dict[str, Any] | None = None,
    contact_email: str | None = None,
) -> dict[str, Any]:
    with session_scope() as session:
        row = session.get(Institution, institution_id)
        if not row:
            raise ValueError("Institution not found")
        if branding is not None:
            if not isinstance(branding, dict):
                raise ValueError("branding must be an object")
            clean = {str(k): v for k, v in branding.items() if isinstance(k, str)}
            row.branding_json = json.dumps(clean, ensure_ascii=True)
        if contact_email is not None:
            row.contact_email = contact_email.strip() or None
        session.flush()
        branding_payload = json.loads(row.branding_json or "{}")
        return {
            "institution_id": institution_id,
            "branding": branding_payload if isinstance(branding_payload, dict) else {},
            "contact_email": row.contact_email,
            "name": row.name,
            "short_name": row.short_name,
            "url": row.website_url,
        }


def list_official_accounts(institution_id: str) -> list[dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(
            select(InstitutionOfficialAccount)
            .where(InstitutionOfficialAccount.institution_id == institution_id)
            .order_by(InstitutionOfficialAccount.id.desc())
        ).scalars().all()
        return [_account_to_dict(row) for row in rows]


def add_official_account(
    institution_id: str,
    *,
    platform: str,
    handle: str,
    url: str | None = None,
    verified: bool = True,
) -> dict[str, Any]:
    if not get_institution(institution_id):
        raise ValueError("Institution not found")
    platform_norm = (platform or "").strip().lower()
    handle_norm = (handle or "").strip()
    if not platform_norm or not handle_norm:
        raise ValueError("platform and handle are required")
    if not handle_norm.startswith("@"):
        handle_norm = f"@{handle_norm.lstrip('@')}"
    with session_scope() as session:
        row = InstitutionOfficialAccount(
            institution_id=institution_id,
            platform=platform_norm,
            handle=handle_norm,
            url=(url or "").strip() or None,
            verified=verified,
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        return _account_to_dict(row)


def delete_official_account(institution_id: str, account_id: int) -> bool:
    with session_scope() as session:
        row = session.get(InstitutionOfficialAccount, account_id)
        if not row or row.institution_id != institution_id:
            return False
        session.delete(row)
        return True


def list_api_keys(institution_id: str, *, include_revoked: bool = False) -> list[dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(
            select(InstitutionApiKey)
            .where(InstitutionApiKey.institution_id == institution_id)
            .order_by(InstitutionApiKey.id.desc())
        ).scalars().all()
        items = []
        for row in rows:
            if row.revoked and not include_revoked:
                continue
            items.append(_api_key_to_dict(row))
        return items


def create_api_key(
    institution_id: str,
    *,
    name: str,
    scopes: list[str] | None = None,
    created_by_user_id: int | None = None,
    expires_at: str | None = None,
) -> dict[str, Any]:
    if not get_institution(institution_id):
        raise ValueError("Institution not found")
    name = (name or "").strip()
    if not name:
        raise ValueError("name is required")
    scopes = scopes or list(DEFAULT_INSTITUTION_SCOPES)
    if not scopes:
        raise ValueError("at least one scope is required")
    raw, prefix, digest = generate_institution_api_key()
    with session_scope() as session:
        row = InstitutionApiKey(
            institution_id=institution_id,
            name=name,
            key_prefix=prefix,
            key_hash=digest,
            scopes_json=json.dumps(scopes, ensure_ascii=True),
            created_by_user_id=created_by_user_id,
            revoked=False,
            expires_at=expires_at,
            last_used_at=None,
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        return _api_key_to_dict(row, include_raw=raw)


def revoke_api_key(institution_id: str, key_id: int) -> dict[str, Any] | None:
    with session_scope() as session:
        row = session.get(InstitutionApiKey, key_id)
        if not row or row.institution_id != institution_id:
            return None
        row.revoked = True
        session.flush()
        return _api_key_to_dict(row)


def authenticate_institution_api_key(raw_key: str) -> dict | None:
    if not raw_key or not raw_key.startswith("msi_"):
        return None
    digest = hash_api_key(raw_key)
    with session_scope() as session:
        row = session.scalar(select(InstitutionApiKey).where(InstitutionApiKey.key_hash == digest))
        if not row or row.revoked:
            return None
        if row.expires_at:
            from datetime import datetime, timezone

            try:
                expires = datetime.fromisoformat(row.expires_at)
                if expires.tzinfo is None:
                    expires = expires.replace(tzinfo=timezone.utc)
                if expires < datetime.now(timezone.utc):
                    return None
            except ValueError:
                return None
        row.last_used_at = now_iso()
        return {
            "id": row.id,
            "name": row.name,
            "institution_id": row.institution_id,
            "partner_org": row.institution_id,
            "scopes": json.loads(row.scopes_json or "[]"),
            "role": "partner",
            "is_active": True,
            "auth_type": "api_key",
            "key_type": "institution",
        }


def list_investigations(institution_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(
            select(InvestigationCase)
            .where(InvestigationCase.institution_id == institution_id)
            .order_by(InvestigationCase.id.desc())
            .limit(min(limit, 200))
        ).scalars().all()
        return [
            {
                "id": row.id,
                "title": row.title,
                "summary": row.summary,
                "status": row.status,
                "priority": row.priority,
                "region": row.region,
                "incident_id": row.incident_id,
                "assigned_to_user_id": row.assigned_to_user_id,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
            for row in rows
        ]


def institution_analytics(institution_id: str) -> dict[str, Any]:
    with session_scope() as session:
        open_statuses = ("open", "ai_analysis", "analyst_review", "institution_review", "decision", "reviewing")
        incident_total = session.scalar(
            select(func.count()).select_from(IncidentReport).where(IncidentReport.institution_id == institution_id)
        ) or 0
        incident_open = session.scalar(
            select(func.count())
            .select_from(IncidentReport)
            .where(
                IncidentReport.institution_id == institution_id,
                IncidentReport.status.in_(open_statuses),
            )
        ) or 0
        case_total = session.scalar(
            select(func.count()).select_from(InvestigationCase).where(InvestigationCase.institution_id == institution_id)
        ) or 0
        case_open = session.scalar(
            select(func.count())
            .select_from(InvestigationCase)
            .where(
                InvestigationCase.institution_id == institution_id,
                InvestigationCase.status.in_(("intake", "investigating", "open")),
            )
        ) or 0
        verified_domains = session.scalar(
            select(func.count())
            .select_from(InstitutionDomain)
            .where(InstitutionDomain.institution_id == institution_id, InstitutionDomain.verified.is_(True))
        ) or 0
        members = session.scalar(
            select(func.count())
            .select_from(InstitutionMembership)
            .where(
                InstitutionMembership.institution_id == institution_id,
                InstitutionMembership.status == "active",
            )
        ) or 0
    return {
        "institution_id": institution_id,
        "incidents_total": int(incident_total),
        "incidents_open": int(incident_open),
        "cases_total": int(case_total),
        "cases_open": int(case_open),
        "verified_domains": int(verified_domains),
        "active_members": int(members),
    }
