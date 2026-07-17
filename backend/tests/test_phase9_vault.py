"""Phase 9 Digital Evidence Vault tests."""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone

from backend.app.db.models import EvidenceItem
from backend.app.db.session import session_scope
from backend.app.vault_store import register_evidence, run_retention, verify_custody_chain
from sqlalchemy import select


def test_register_transfer_export_and_verify(client):
    test_client, _ = client
    content = b"screenshot-bytes-for-case-evidence"
    payload = {
        "title": "WhatsApp screenshot",
        "filename": "scam.png",
        "content_base64": base64.b64encode(content).decode("ascii"),
        "content_type": "image/png",
        "description": "Citizen-submitted screenshot",
        "case_id": 1,
    }
    created = test_client.post("/api/v1/evidence", json=payload)
    assert created.status_code == 200, created.text
    body = created.json()
    evidence_id = body["evidence_id"]
    assert body["sha256"]
    assert body["size_bytes"] == len(content)
    assert body["case_id"] == 1

    listed = test_client.get("/api/v1/evidence?case_id=1")
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1

    custody = test_client.get(f"/api/v1/evidence/{evidence_id}/custody")
    assert custody.status_code == 200
    assert custody.json()["chain"]["valid"] is True
    assert any(event["event_type"] == "registered" for event in custody.json()["events"])

    transferred = test_client.post(
        f"/api/v1/evidence/{evidence_id}/transfer",
        json={"to_user_id": 42, "note": "Hand to lead analyst"},
    )
    assert transferred.status_code == 200
    assert transferred.json()["custodian_user_id"] == 42

    downloaded = test_client.get(f"/api/v1/evidence/{evidence_id}/download")
    assert downloaded.status_code == 200
    assert downloaded.content == content

    exported = test_client.post(f"/api/v1/evidence/{evidence_id}/export")
    assert exported.status_code == 200
    export_body = exported.json()
    assert export_body["signature_valid"] is True
    export_id = export_body["export_id"]

    verified = test_client.get(f"/api/v1/evidence/exports/{export_id}/verify")
    assert verified.status_code == 200
    assert verified.json()["valid"] is True

    chain = verify_custody_chain(evidence_id)
    assert chain["valid"] is True
    assert chain["events"] >= 3


def test_retention_dry_run_and_purge(client):
    test_client, tmp_path = client
    item = register_evidence(
        title="Expired memo",
        filename="memo.txt",
        content=b"old evidence",
        content_type="text/plain",
        retention_days=0,
    )
    evidence_id = item["evidence_id"]
    past = (datetime.now(timezone.utc) - timedelta(days=2)).replace(microsecond=0).isoformat()
    with session_scope() as session:
        row = session.execute(
            select(EvidenceItem).where(EvidenceItem.evidence_id == evidence_id)
        ).scalar_one()
        row.retention_until = past

    dry = test_client.post("/api/v1/evidence/retention/run", json={"dry_run": True})
    assert dry.status_code == 200
    assert dry.json()["dry_run"] is True
    assert dry.json()["count"] >= 1

    purged = run_retention(dry_run=False)
    assert purged["dry_run"] is False
    assert any(entry["evidence_id"] == evidence_id for entry in purged["items"])

    got = test_client.get(f"/api/v1/evidence/{evidence_id}")
    assert got.status_code == 200
    assert got.json()["status"] == "purged"


def test_health_reports_phase9_version(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "1.9.0"
    assert health["vault"] is True
