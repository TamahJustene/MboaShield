"""Digital Evidence Vault persistence, custody, export, and retention."""

from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import or_, select

from .core.config import get_settings
from .db.models import EvidenceCustodyEvent, EvidenceExport, EvidenceItem
from .db.session import session_scope
from .repositories import now_iso
from .services.vault.signing import custody_event_hash, sha256_hex, sign_payload, verify_signature
from .services.vault.storage import get_storage_adapter


def _iso_plus_days(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).replace(microsecond=0).isoformat()


def _item_to_dict(row: EvidenceItem) -> dict[str, Any]:
    return {
        "id": row.id,
        "evidence_id": row.evidence_id,
        "title": row.title,
        "description": row.description,
        "content_type": row.content_type,
        "filename": row.filename,
        "size_bytes": row.size_bytes,
        "sha256": row.sha256,
        "storage_backend": row.storage_backend,
        "storage_key": row.storage_key,
        "case_id": row.case_id,
        "incident_id": row.incident_id,
        "verification_check_id": row.verification_check_id,
        "custodian_user_id": row.custodian_user_id,
        "status": row.status,
        "retention_until": row.retention_until,
        "created_by_user_id": row.created_by_user_id,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _custody_to_dict(row: EvidenceCustodyEvent) -> dict[str, Any]:
    return {
        "id": row.id,
        "evidence_id": row.evidence_id,
        "event_type": row.event_type,
        "from_user_id": row.from_user_id,
        "to_user_id": row.to_user_id,
        "note": row.note,
        "details": json.loads(row.details_json or "{}"),
        "event_hash": row.event_hash,
        "prev_event_hash": row.prev_event_hash,
        "created_at": row.created_at,
    }


def _append_custody(
    session,
    *,
    evidence_id: str,
    event_type: str,
    from_user_id: int | None = None,
    to_user_id: int | None = None,
    note: str | None = None,
    details: dict[str, Any] | None = None,
) -> EvidenceCustodyEvent:
    prev = session.execute(
        select(EvidenceCustodyEvent)
        .where(EvidenceCustodyEvent.evidence_id == evidence_id)
        .order_by(EvidenceCustodyEvent.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    created_at = now_iso()
    prev_hash = prev.event_hash if prev else None
    event_hash = custody_event_hash(
        evidence_id=evidence_id,
        event_type=event_type,
        created_at=created_at,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        note=note,
        prev_event_hash=prev_hash,
    )
    row = EvidenceCustodyEvent(
        evidence_id=evidence_id,
        event_type=event_type,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        note=note,
        details_json=json.dumps(details or {}),
        event_hash=event_hash,
        prev_event_hash=prev_hash,
        created_at=created_at,
    )
    session.add(row)
    return row


def register_evidence(
    *,
    title: str,
    filename: str,
    content: bytes,
    content_type: str = "application/octet-stream",
    description: str | None = None,
    case_id: int | None = None,
    incident_id: int | None = None,
    verification_check_id: int | None = None,
    created_by_user_id: int | None = None,
    retention_days: int | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    if not settings.vault_enabled:
        raise ValueError("VAULT_ENABLED is false")
    max_bytes = int(settings.vault_max_bytes)
    if len(content) > max_bytes:
        raise ValueError(f"Evidence exceeds VAULT_MAX_BYTES ({max_bytes})")
    if not content:
        raise ValueError("Evidence content is empty")

    evidence_id = f"evd_{uuid.uuid4().hex[:20]}"
    digest = sha256_hex(content)
    storage = get_storage_adapter()
    key = f"{evidence_id}/{filename}"
    storage.put(key, content, content_type=content_type)
    days = retention_days if retention_days is not None else int(settings.vault_retention_days)
    now = now_iso()

    with session_scope() as session:
        row = EvidenceItem(
            evidence_id=evidence_id,
            title=title,
            description=description,
            content_type=content_type,
            filename=filename,
            size_bytes=len(content),
            sha256=digest,
            storage_backend=storage.backend,
            storage_key=key,
            case_id=case_id,
            incident_id=incident_id,
            verification_check_id=verification_check_id,
            custodian_user_id=created_by_user_id,
            status="active",
            retention_until=_iso_plus_days(days),
            created_by_user_id=created_by_user_id,
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        session.flush()
        _append_custody(
            session,
            evidence_id=evidence_id,
            event_type="registered",
            to_user_id=created_by_user_id,
            note="Evidence registered in vault",
            details={"sha256": digest, "size_bytes": len(content)},
        )
        session.flush()
        return _item_to_dict(row)


def register_evidence_from_base64(
    *,
    title: str,
    filename: str,
    content_base64: str,
    content_type: str = "application/octet-stream",
    description: str | None = None,
    case_id: int | None = None,
    incident_id: int | None = None,
    verification_check_id: int | None = None,
    created_by_user_id: int | None = None,
    retention_days: int | None = None,
) -> dict[str, Any]:
    try:
        content = base64.b64decode(content_base64, validate=True)
    except Exception as exc:
        raise ValueError("Invalid base64 content") from exc
    return register_evidence(
        title=title,
        filename=filename,
        content=content,
        content_type=content_type,
        description=description,
        case_id=case_id,
        incident_id=incident_id,
        verification_check_id=verification_check_id,
        created_by_user_id=created_by_user_id,
        retention_days=retention_days,
    )


def get_evidence(evidence_id: str) -> dict[str, Any] | None:
    with session_scope() as session:
        row = session.execute(
            select(EvidenceItem).where(EvidenceItem.evidence_id == evidence_id)
        ).scalar_one_or_none()
        return _item_to_dict(row) if row else None


def list_evidence(
    *,
    case_id: int | None = None,
    incident_id: int | None = None,
    q: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    with session_scope() as session:
        stmt = select(EvidenceItem).order_by(EvidenceItem.id.desc()).limit(min(limit, 200))
        if case_id is not None:
            stmt = stmt.where(EvidenceItem.case_id == case_id)
        if incident_id is not None:
            stmt = stmt.where(EvidenceItem.incident_id == incident_id)
        if status:
            stmt = stmt.where(EvidenceItem.status == status)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(
                    EvidenceItem.title.ilike(like),
                    EvidenceItem.filename.ilike(like),
                    EvidenceItem.evidence_id.ilike(like),
                    EvidenceItem.sha256.ilike(like),
                )
            )
        rows = session.execute(stmt).scalars().all()
        return [_item_to_dict(row) for row in rows]


def read_evidence_bytes(evidence_id: str) -> tuple[dict[str, Any], bytes]:
    item = get_evidence(evidence_id)
    if not item:
        raise ValueError("Evidence not found")
    if item["status"] == "purged":
        raise ValueError("Evidence has been purged")
    storage = get_storage_adapter()
    data = storage.get(item["storage_key"])
    if sha256_hex(data) != item["sha256"]:
        raise ValueError("Evidence integrity check failed (hash mismatch)")
    return item, data


def list_custody(evidence_id: str) -> list[dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(
            select(EvidenceCustodyEvent)
            .where(EvidenceCustodyEvent.evidence_id == evidence_id)
            .order_by(EvidenceCustodyEvent.id.asc())
        ).scalars().all()
        return [_custody_to_dict(row) for row in rows]


def verify_custody_chain(evidence_id: str) -> dict[str, Any]:
    events = list_custody(evidence_id)
    ok = True
    prev = None
    for event in events:
        expected = custody_event_hash(
            evidence_id=event["evidence_id"],
            event_type=event["event_type"],
            created_at=event["created_at"],
            from_user_id=event["from_user_id"],
            to_user_id=event["to_user_id"],
            note=event["note"],
            prev_event_hash=event["prev_event_hash"],
        )
        if expected != event["event_hash"] or event["prev_event_hash"] != prev:
            ok = False
            break
        prev = event["event_hash"]
    return {"evidence_id": evidence_id, "events": len(events), "valid": ok}


def transfer_custody(
    evidence_id: str,
    *,
    to_user_id: int,
    from_user_id: int | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    with session_scope() as session:
        row = session.execute(
            select(EvidenceItem).where(EvidenceItem.evidence_id == evidence_id)
        ).scalar_one_or_none()
        if not row:
            raise ValueError("Evidence not found")
        if row.status != "active":
            raise ValueError(f"Cannot transfer evidence in status '{row.status}'")
        previous = row.custodian_user_id
        row.custodian_user_id = to_user_id
        row.updated_at = now_iso()
        _append_custody(
            session,
            evidence_id=evidence_id,
            event_type="transferred",
            from_user_id=from_user_id if from_user_id is not None else previous,
            to_user_id=to_user_id,
            note=note or "Custody transferred",
        )
        session.flush()
        return _item_to_dict(row)


def export_evidence(
    evidence_id: str,
    *,
    created_by_user_id: int | None = None,
    include_content: bool = True,
) -> dict[str, Any]:
    item, data = read_evidence_bytes(evidence_id)
    custody = list_custody(evidence_id)
    package = {
        "export_type": "mboashield_evidence_package",
        "exported_at": now_iso(),
        "evidence": item,
        "custody_chain": custody,
        "content_base64": base64.b64encode(data).decode("ascii") if include_content else None,
        "content_included": include_content,
    }
    package_body = json.dumps(package, sort_keys=True, separators=(",", ":")).encode("utf-8")
    package_sha = sha256_hex(package_body)
    signature = sign_payload(package_body)
    export_id = f"exp_{uuid.uuid4().hex[:16]}"
    storage = get_storage_adapter()
    key = f"exports/{export_id}.json"
    storage.put(key, package_body, content_type="application/json")

    with session_scope() as session:
        row = EvidenceExport(
            export_id=export_id,
            evidence_id=evidence_id,
            format="json_package",
            package_sha256=package_sha,
            signature=signature,
            storage_key=key,
            created_by_user_id=created_by_user_id,
            created_at=now_iso(),
        )
        session.add(row)
        _append_custody(
            session,
            evidence_id=evidence_id,
            event_type="exported",
            from_user_id=created_by_user_id,
            note="Signed export package created",
            details={"export_id": export_id, "package_sha256": package_sha},
        )
        session.flush()

    return {
        "export_id": export_id,
        "evidence_id": evidence_id,
        "package_sha256": package_sha,
        "signature": signature,
        "signature_valid": verify_signature(package_body, signature),
        "package": package,
    }


def verify_export(export_id: str) -> dict[str, Any]:
    with session_scope() as session:
        row = session.execute(
            select(EvidenceExport).where(EvidenceExport.export_id == export_id)
        ).scalar_one_or_none()
        if not row:
            raise ValueError("Export not found")
        storage = get_storage_adapter()
        body = storage.get(row.storage_key)
        package_sha = sha256_hex(body)
        sig_ok = verify_signature(body, row.signature)
        return {
            "export_id": export_id,
            "evidence_id": row.evidence_id,
            "package_sha256": package_sha,
            "stored_package_sha256": row.package_sha256,
            "hash_match": package_sha == row.package_sha256,
            "signature_valid": sig_ok,
            "valid": sig_ok and package_sha == row.package_sha256,
        }


def run_retention(*, dry_run: bool = True) -> dict[str, Any]:
    """Purge expired active evidence (object + status). Custody events remain."""
    now = now_iso()
    candidates: list[dict[str, Any]] = []
    with session_scope() as session:
        rows = session.execute(
            select(EvidenceItem).where(
                EvidenceItem.status == "active",
                EvidenceItem.retention_until.is_not(None),
                EvidenceItem.retention_until <= now,
            )
        ).scalars().all()
        for row in rows:
            candidates.append(_item_to_dict(row))
            if dry_run:
                continue
            storage = get_storage_adapter()
            try:
                storage.delete(row.storage_key)
            except Exception:
                pass
            row.status = "purged"
            row.updated_at = now_iso()
            _append_custody(
                session,
                evidence_id=row.evidence_id,
                event_type="retention_purged",
                note="Purged by retention policy",
                details={"retention_until": row.retention_until},
            )
    return {
        "dry_run": dry_run,
        "count": len(candidates),
        "items": [{"evidence_id": item["evidence_id"], "retention_until": item["retention_until"]} for item in candidates],
    }
