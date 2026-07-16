"""Verified government announcements: lifecycle, signing, verification, certificates."""

from __future__ import annotations

import json
import uuid
from typing import Any
from urllib.parse import urljoin

from sqlalchemy import select

from .core.config import get_settings
from .db.models import AnnouncementVersion, GovernmentAnnouncement
from .db.session import session_scope
from .repositories import get_institution, now_iso
from .services.announcements.signing import (
    sign_announcement_payload,
    signing_kid,
    verify_announcement_payload,
)


def _announcement_row_to_dict(row: GovernmentAnnouncement) -> dict[str, Any]:
    return {
        "id": row.id,
        "announcement_id": row.announcement_id,
        "institution_id": row.institution_id,
        "title": row.title,
        "status": row.status,
        "current_version": row.current_version,
        "locale": row.locale,
        "created_by_user_id": row.created_by_user_id,
        "published_by_user_id": row.published_by_user_id,
        "published_at": row.published_at,
        "revoked_at": row.revoked_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "verify_path": f"/verify/a/{row.announcement_id}",
    }


def _version_to_dict(row: AnnouncementVersion) -> dict[str, Any]:
    return {
        "id": row.id,
        "announcement_id": row.announcement_id,
        "version_number": row.version_number,
        "title": row.title,
        "body": row.body,
        "content_hash": row.content_hash,
        "signature": row.signature,
        "signing_kid": row.signing_kid,
        "published_at": row.published_at,
        "published_by_user_id": row.published_by_user_id,
        "created_at": row.created_at,
    }


def _signable_payload(
    *,
    announcement_id: str,
    institution_id: str,
    version_number: int,
    title: str,
    body: str,
    locale: str,
    published_at: str,
) -> dict[str, Any]:
    return {
        "announcement_id": announcement_id,
        "institution_id": institution_id,
        "version": version_number,
        "title": title,
        "body": body,
        "locale": locale,
        "published_at": published_at,
        "issuer": "MboaShield Verified Communications",
    }


def public_base_url() -> str:
    settings = get_settings()
    base = (settings.public_base_url or "").strip().rstrip("/")
    if base:
        return base
    return "http://127.0.0.1:8000"


def verify_url(announcement_id: str) -> str:
    return urljoin(public_base_url() + "/", f"verify/a/{announcement_id}")


def create_announcement_draft(
    *,
    institution_id: str,
    title: str,
    body: str,
    locale: str = "fr",
    created_by_user_id: int | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    if not settings.verified_comms_enabled:
        raise ValueError("VERIFIED_COMMS_ENABLED is false")
    if not get_institution(institution_id):
        raise ValueError("Institution not found")
    title = (title or "").strip()
    body = (body or "").strip()
    if len(title) < 3:
        raise ValueError("title is required")
    if len(body) < 10:
        raise ValueError("body must be at least 10 characters")
    announcement_id = f"ann_{uuid.uuid4().hex[:18]}"
    now = now_iso()
    with session_scope() as session:
        row = GovernmentAnnouncement(
            announcement_id=announcement_id,
            institution_id=institution_id,
            title=title,
            status="draft",
            current_version=0,
            locale=locale or "fr",
            created_by_user_id=created_by_user_id,
            published_by_user_id=None,
            published_at=None,
            revoked_at=None,
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        session.flush()
        # stash draft body on a pseudo-version 0 in memory only via updated title - actually store draft body in announcement title only
        # For draft we keep body in a hidden field - add draft_body_json column? Simpler: store draft in first unpublished version record optional
        # Use announcement_versions only on publish; for draft store body in a JSON column - skip migration: use AnnouncementVersion with version_number=0 draft flag
        draft_version = AnnouncementVersion(
            announcement_id=announcement_id,
            version_number=0,
            title=title,
            body=body,
            content_hash="draft",
            signature="draft",
            signing_kid="draft",
            published_at=now,
            published_by_user_id=None,
            created_at=now,
        )
        session.add(draft_version)
        session.flush()
        return _announcement_row_to_dict(row)


def update_draft(
    announcement_id: str,
    *,
    title: str | None = None,
    body: str | None = None,
    locale: str | None = None,
) -> dict[str, Any]:
    with session_scope() as session:
        row = session.execute(
            select(GovernmentAnnouncement).where(GovernmentAnnouncement.announcement_id == announcement_id)
        ).scalar_one_or_none()
        if not row:
            raise ValueError("Announcement not found")
        if row.status != "draft":
            raise ValueError("Only draft announcements can be edited")
        if title is not None:
            row.title = title.strip()
        if locale is not None:
            row.locale = locale.strip() or row.locale
        row.updated_at = now_iso()
        if body is not None:
            draft = session.execute(
                select(AnnouncementVersion).where(
                    AnnouncementVersion.announcement_id == announcement_id,
                    AnnouncementVersion.version_number == 0,
                )
            ).scalar_one_or_none()
            if draft:
                draft.body = body.strip()
                draft.title = row.title
        session.flush()
        return _announcement_row_to_dict(row)


def publish_announcement(
    announcement_id: str,
    *,
    published_by_user_id: int | None = None,
    title: str | None = None,
    body: str | None = None,
) -> dict[str, Any]:
    with session_scope() as session:
        row = session.execute(
            select(GovernmentAnnouncement).where(GovernmentAnnouncement.announcement_id == announcement_id)
        ).scalar_one_or_none()
        if not row:
            raise ValueError("Announcement not found")
        if row.status == "revoked":
            raise ValueError("Revoked announcements cannot be published")
        draft = session.execute(
            select(AnnouncementVersion).where(
                AnnouncementVersion.announcement_id == announcement_id,
                AnnouncementVersion.version_number == 0,
            )
        ).scalar_one_or_none()
        final_title = (title or row.title or (draft.title if draft else "")).strip()
        final_body = (body or (draft.body if draft else "")).strip()
        if len(final_body) < 10:
            raise ValueError("body must be at least 10 characters")
        new_version = row.current_version + 1 if row.status == "published" else 1
        published_at = now_iso()
        signable = _signable_payload(
            announcement_id=announcement_id,
            institution_id=row.institution_id,
            version_number=new_version,
            title=final_title,
            body=final_body,
            locale=row.locale,
            published_at=published_at,
        )
        content_hash, signature = sign_announcement_payload(signable)
        version_row = AnnouncementVersion(
            announcement_id=announcement_id,
            version_number=new_version,
            title=final_title,
            body=final_body,
            content_hash=content_hash,
            signature=signature,
            signing_kid=signing_kid(),
            published_at=published_at,
            published_by_user_id=published_by_user_id,
            created_at=published_at,
        )
        session.add(version_row)
        row.title = final_title
        row.status = "published"
        row.current_version = new_version
        row.published_at = published_at
        row.published_by_user_id = published_by_user_id
        row.updated_at = published_at
        session.flush()
        payload = _announcement_row_to_dict(row)
        payload["version"] = _version_to_dict(version_row)
        payload["verify_url"] = verify_url(announcement_id)
        payload["qr"] = build_qr_payload(announcement_id, version_number=new_version)
        return payload


def revoke_announcement(announcement_id: str) -> dict[str, Any]:
    with session_scope() as session:
        row = session.execute(
            select(GovernmentAnnouncement).where(GovernmentAnnouncement.announcement_id == announcement_id)
        ).scalar_one_or_none()
        if not row:
            raise ValueError("Announcement not found")
        if row.status != "published":
            raise ValueError("Only published announcements can be revoked")
        now = now_iso()
        row.status = "revoked"
        row.revoked_at = now
        row.updated_at = now
        session.flush()
        return _announcement_row_to_dict(row)


def get_announcement(announcement_id: str) -> dict[str, Any] | None:
    with session_scope() as session:
        row = session.execute(
            select(GovernmentAnnouncement).where(GovernmentAnnouncement.announcement_id == announcement_id)
        ).scalar_one_or_none()
        return _announcement_row_to_dict(row) if row else None


def list_announcements(
    *,
    institution_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    with session_scope() as session:
        stmt = select(GovernmentAnnouncement).order_by(GovernmentAnnouncement.id.desc()).limit(min(limit, 200))
        if institution_id:
            stmt = stmt.where(GovernmentAnnouncement.institution_id == institution_id)
        if status:
            stmt = stmt.where(GovernmentAnnouncement.status == status)
        rows = session.execute(stmt).scalars().all()
        return [_announcement_row_to_dict(row) for row in rows]


def list_versions(announcement_id: str) -> list[dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(
            select(AnnouncementVersion)
            .where(
                AnnouncementVersion.announcement_id == announcement_id,
                AnnouncementVersion.version_number > 0,
            )
            .order_by(AnnouncementVersion.version_number.asc())
        ).scalars().all()
        return [_version_to_dict(row) for row in rows]


def get_version(announcement_id: str, version_number: int) -> dict[str, Any] | None:
    with session_scope() as session:
        row = session.execute(
            select(AnnouncementVersion).where(
                AnnouncementVersion.announcement_id == announcement_id,
                AnnouncementVersion.version_number == version_number,
            )
        ).scalar_one_or_none()
        return _version_to_dict(row) if row else None


def get_announcement_detail(announcement_id: str) -> dict[str, Any] | None:
    announcement = get_announcement(announcement_id)
    if not announcement:
        return None
    draft = get_version(announcement_id, 0)
    versions = list_versions(announcement_id)
    latest = get_version(announcement_id, announcement["current_version"]) if announcement["current_version"] else None
    return {
        **announcement,
        "draft_body": draft.get("body") if draft and announcement["status"] == "draft" else None,
        "versions": versions,
        "latest_published": latest,
        "verify_url": verify_url(announcement_id),
    }


def verify_announcement(
    announcement_id: str,
    *,
    version_number: int | None = None,
) -> dict[str, Any]:
    announcement = get_announcement(announcement_id)
    if not announcement:
        raise ValueError("Announcement not found")
    if announcement["status"] == "revoked":
        return {
            "valid": False,
            "announcement_id": announcement_id,
            "status": "revoked",
            "message": "This announcement has been revoked by the issuing institution.",
            "verify_url": verify_url(announcement_id),
        }
    if announcement["status"] == "draft":
        return {
            "valid": False,
            "announcement_id": announcement_id,
            "status": "draft",
            "message": "This announcement is not published yet.",
            "verify_url": verify_url(announcement_id),
        }
    version_no = version_number or announcement["current_version"]
    version = get_version(announcement_id, version_no)
    if not version:
        raise ValueError("Version not found")
    institution = get_institution(announcement["institution_id"])
    signable = _signable_payload(
        announcement_id=announcement_id,
        institution_id=announcement["institution_id"],
        version_number=version["version_number"],
        title=version["title"],
        body=version["body"],
        locale=announcement.get("locale") or "fr",
        published_at=version["published_at"],
    )
    sig_ok = verify_announcement_payload(
        signable,
        content_hash=version["content_hash"],
        signature=version["signature"],
    )
    return {
        "valid": sig_ok and announcement["status"] == "published",
        "announcement_id": announcement_id,
        "status": announcement["status"],
        "version": version["version_number"],
        "title": version["title"],
        "body": version["body"],
        "published_at": version["published_at"],
        "content_hash": version["content_hash"],
        "signature": version["signature"],
        "signing_kid": version["signing_kid"],
        "signature_valid": sig_ok,
        "institution": institution,
        "verify_url": verify_url(announcement_id),
        "authenticity": "verified" if sig_ok else "failed",
        "certainty": "none",
    }


def build_qr_payload(announcement_id: str, *, version_number: int | None = None) -> dict[str, Any]:
    announcement = get_announcement(announcement_id)
    if not announcement:
        raise ValueError("Announcement not found")
    version_no = version_number or announcement.get("current_version") or 0
    url = verify_url(announcement_id)
    if version_no:
        url = f"{url}?v={version_no}"
    return {
        "type": "mboashield_announcement_verify",
        "announcement_id": announcement_id,
        "version": version_no,
        "verify_url": url,
        "institution_id": announcement.get("institution_id"),
    }


def build_certificate(
    announcement_id: str,
    *,
    version_number: int | None = None,
) -> dict[str, Any]:
    verification = verify_announcement(announcement_id, version_number=version_number)
    announcement = get_announcement(announcement_id)
    institution = get_institution(announcement["institution_id"]) if announcement else None
    return {
        "certificate_type": "mboashield_authenticity_certificate",
        "issued_at": now_iso(),
        "founder": "Justene Nkwagoh Tamah",
        "platform": "MboaShield",
        "verification": verification,
        "institution": institution,
        "permanent_verify_url": verify_url(announcement_id),
        "qr": build_qr_payload(
            announcement_id,
            version_number=verification.get("version") if verification.get("version") else None,
        ),
    }


def certificate_markdown(certificate: dict[str, Any]) -> str:
    verification = certificate.get("verification") or {}
    institution = certificate.get("institution") or {}
    lines = [
        "# MboaShield Authenticity Certificate",
        "",
        f"**Announcement:** {verification.get('announcement_id')}",
        f"**Title:** {verification.get('title')}",
        f"**Institution:** {institution.get('name', 'Unknown')}",
        f"**Version:** {verification.get('version')}",
        f"**Published:** {verification.get('published_at')}",
        f"**Valid:** {verification.get('valid')}",
        f"**Signature valid:** {verification.get('signature_valid')}",
        "",
        f"Permanent verify URL: {certificate.get('permanent_verify_url')}",
        "",
        "---",
        verification.get("body") or "",
    ]
    return "\n".join(lines)
