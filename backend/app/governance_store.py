"""Governance persistence: consent, risk register, cards, controls (Phase 14)."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select

from .db.models import ConsentRecord, DatasetCard, GovernanceControl, ModelCard, RiskRegisterEntry
from .db.session import session_scope
from .repositories import now_iso

OPTIONAL_FEATURES = {
    "analytics_share": "Share anonymized check outcomes for national analytics",
    "feedback_learning": "Allow analyst feedback to improve calibration",
    "partner_notify": "Optional partner institution notifications for high-risk checks",
}

DEFAULT_RISKS: list[dict[str, str]] = [
    {
        "risk_id": "RISK-AI-01",
        "title": "Overconfidence in trust scores",
        "category": "ai",
        "threat_model_ref": "TM-AI-OVERCONFIDENCE",
        "likelihood": "medium",
        "impact": "high",
        "status": "mitigated",
        "owner": "AI Governance",
        "mitigation": "certainty remains none; model cards state decision-support only",
        "residual_risk": "low",
    },
    {
        "risk_id": "RISK-AI-02",
        "title": "Language or region bias",
        "category": "ai",
        "threat_model_ref": "TM-AI-BIAS",
        "likelihood": "medium",
        "impact": "medium",
        "status": "open",
        "owner": "AI Governance",
        "mitigation": "EN/FR golden evaluation sets; human review gates",
        "residual_risk": "medium",
    },
    {
        "risk_id": "RISK-ID-01",
        "title": "Stolen credentials / session takeover",
        "category": "identity",
        "threat_model_ref": "TM-SPOOF-PASSWORD",
        "likelihood": "medium",
        "impact": "high",
        "status": "mitigated",
        "owner": "Digital Identity",
        "mitigation": "MFA, lockout, session revoke, short JWT TTL",
        "residual_risk": "medium",
    },
    {
        "risk_id": "RISK-EV-01",
        "title": "Evidence tampering",
        "category": "evidence",
        "threat_model_ref": "TM-TAMPER-EVIDENCE",
        "likelihood": "medium",
        "impact": "critical",
        "status": "mitigated",
        "owner": "Cybersecurity",
        "mitigation": "Hash + custody chain + retention controls",
        "residual_risk": "low",
    },
    {
        "risk_id": "RISK-PRIV-01",
        "title": "Citizen PII oversharing",
        "category": "privacy",
        "threat_model_ref": "TM-DISCLOSE-PII",
        "likelihood": "medium",
        "impact": "high",
        "status": "open",
        "owner": "AI Governance",
        "mitigation": "Consent records for optional features; RBAC on audit",
        "residual_risk": "medium",
    },
]

DEFAULT_CONTROLS: list[dict[str, str]] = [
    {
        "control_id": "CTL-AI-CERTAINTY",
        "title": "No default certainty claims",
        "category": "responsible_ai",
        "status": "implemented",
        "description": "Trust fusion must emit certainty=none unless a calibrated model card overrides.",
        "evidence": "trust_fusion + engine package policy",
    },
    {
        "control_id": "CTL-AI-HUMAN",
        "title": "Human gate before public advisory",
        "category": "responsible_ai",
        "status": "implemented",
        "description": "Incident workflow requires human decision before public_advisory.",
        "evidence": "incident_workflow states",
    },
    {
        "control_id": "CTL-PRIV-CONSENT",
        "title": "Consent for optional citizen features",
        "category": "privacy",
        "status": "implemented",
        "description": "Optional analytics/feedback/partner features require recorded consent.",
        "evidence": "consent_records API",
    },
    {
        "control_id": "CTL-COMP-AUDIT",
        "title": "Audit trail for privileged actions",
        "category": "compliance",
        "status": "implemented",
        "description": "Privileged mutations write audit logs with actor role.",
        "evidence": "audit_logs + /api/v1/audit/logs",
    },
]

# Assessable mappings (not certification). T7.
CONTROL_FRAMEWORK_MAP: dict[str, dict[str, list[str]]] = {
    "CTL-AI-CERTAINTY": {
        "iso27001": ["A.8.28", "A.5.8"],
        "nist_csf": ["ID.RA-01", "GV.RM-01"],
    },
    "CTL-AI-HUMAN": {
        "iso27001": ["A.5.2", "A.5.36"],
        "nist_csf": ["GV.OV-01", "DE.CM-01"],
    },
    "CTL-PRIV-CONSENT": {
        "iso27001": ["A.5.34", "A.8.11"],
        "nist_csf": ["GV.OC-03", "PR.DS-01"],
    },
    "CTL-COMP-AUDIT": {
        "iso27001": ["A.8.15", "A.5.33"],
        "nist_csf": ["ID.IM-01", "DE.AE-03"],
    },
}


def framework_map() -> dict[str, Any]:
    controls = list_controls()
    mapped = []
    for item in controls:
        cid = item["control_id"]
        frameworks = CONTROL_FRAMEWORK_MAP.get(cid, {"iso27001": [], "nist_csf": []})
        mapped.append({**item, "frameworks": frameworks})
    return {
        "note": "Framework IDs are assessable mappings, not ISO/NIST certification.",
        "controls": mapped,
        "count": len(mapped),
        "frameworks_supported": ["iso27001", "nist_csf"],
    }

DEFAULT_MODEL_CARDS: list[dict[str, Any]] = [
    {
        "card_id": "mc-text-nlp-v1",
        "model_id": "mboashield-text-nlp-v1",
        "title": "MboaShield Text NLP v1",
        "version": "1.0",
        "summary": "Heuristic text risk signals for scam/urgency patterns.",
        "intended_use": "Decision support for analysts and citizen checks.",
        "limitations": "Not a legal determination; EN/FR biased toward demo corpora.",
        "certainty_policy": "none",
        "body": {"modalities": ["text"], "fallback": "heuristic"},
    },
    {
        "card_id": "mc-media-v1",
        "model_id": "mboashield-media-adapter-v1",
        "title": "MboaShield Media Adapter v1",
        "version": "1.0",
        "summary": "Media metadata and lightweight risk cues.",
        "intended_use": "Screen uploaded media before analyst review.",
        "limitations": "Not a deepfake detector of record; scaffold ONNX path may fall back.",
        "certainty_policy": "none",
        "body": {"modalities": ["image", "video"], "fallback": "heuristic"},
    },
]

DEFAULT_DATASET_CARDS: list[dict[str, Any]] = [
    {
        "card_id": "dc-golden-en",
        "dataset_id": "ai_golden_en",
        "title": "EN golden evaluation set",
        "version": "1.0",
        "summary": "Synthetic English cases for engine regression.",
        "provenance": "Curated by MboaShield for Phase 12 evaluation; not citizen data.",
        "languages": "en",
        "body": {"path": "data/ai_golden_en.json"},
    },
    {
        "card_id": "dc-golden-fr",
        "dataset_id": "ai_golden_fr",
        "title": "FR golden evaluation set",
        "version": "1.0",
        "summary": "Synthetic French cases for engine regression.",
        "provenance": "Curated by MboaShield for Phase 12 evaluation; not citizen data.",
        "languages": "fr",
        "body": {"path": "data/ai_golden_fr.json"},
    },
]


def _consent_dict(row: ConsentRecord) -> dict[str, Any]:
    return {
        "id": row.id,
        "subject_key": row.subject_key,
        "user_id": row.user_id,
        "feature": row.feature,
        "granted": bool(row.granted),
        "purpose": row.purpose,
        "policy_version": row.policy_version,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _risk_dict(row: RiskRegisterEntry) -> dict[str, Any]:
    return {
        "risk_id": row.risk_id,
        "title": row.title,
        "category": row.category,
        "threat_model_ref": row.threat_model_ref,
        "likelihood": row.likelihood,
        "impact": row.impact,
        "status": row.status,
        "owner": row.owner,
        "mitigation": row.mitigation,
        "residual_risk": row.residual_risk,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _model_card_dict(row: ModelCard) -> dict[str, Any]:
    return {
        "card_id": row.card_id,
        "model_id": row.model_id,
        "title": row.title,
        "version": row.version,
        "summary": row.summary,
        "intended_use": row.intended_use,
        "limitations": row.limitations,
        "certainty_policy": row.certainty_policy,
        "body": json.loads(row.body_json or "{}"),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _dataset_card_dict(row: DatasetCard) -> dict[str, Any]:
    return {
        "card_id": row.card_id,
        "dataset_id": row.dataset_id,
        "title": row.title,
        "version": row.version,
        "summary": row.summary,
        "provenance": row.provenance,
        "languages": row.languages,
        "body": json.loads(row.body_json or "{}"),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _control_dict(row: GovernanceControl) -> dict[str, Any]:
    return {
        "control_id": row.control_id,
        "title": row.title,
        "category": row.category,
        "status": row.status,
        "description": row.description,
        "evidence": row.evidence,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def ensure_governance_seed() -> None:
    now = now_iso()
    with session_scope() as session:
        for item in DEFAULT_RISKS:
            exists = session.execute(
                select(RiskRegisterEntry).where(RiskRegisterEntry.risk_id == item["risk_id"])
            ).scalar_one_or_none()
            if exists:
                continue
            session.add(
                RiskRegisterEntry(
                    risk_id=item["risk_id"],
                    title=item["title"],
                    category=item["category"],
                    threat_model_ref=item["threat_model_ref"],
                    likelihood=item["likelihood"],
                    impact=item["impact"],
                    status=item["status"],
                    owner=item["owner"],
                    mitigation=item["mitigation"],
                    residual_risk=item["residual_risk"],
                    created_at=now,
                    updated_at=now,
                )
            )
        for item in DEFAULT_CONTROLS:
            exists = session.execute(
                select(GovernanceControl).where(GovernanceControl.control_id == item["control_id"])
            ).scalar_one_or_none()
            if exists:
                continue
            session.add(
                GovernanceControl(
                    control_id=item["control_id"],
                    title=item["title"],
                    category=item["category"],
                    status=item["status"],
                    description=item["description"],
                    evidence=item["evidence"],
                    created_at=now,
                    updated_at=now,
                )
            )
        for item in DEFAULT_MODEL_CARDS:
            exists = session.execute(
                select(ModelCard).where(ModelCard.card_id == item["card_id"])
            ).scalar_one_or_none()
            if exists:
                continue
            session.add(
                ModelCard(
                    card_id=item["card_id"],
                    model_id=item["model_id"],
                    title=item["title"],
                    version=item["version"],
                    summary=item["summary"],
                    intended_use=item["intended_use"],
                    limitations=item["limitations"],
                    certainty_policy=item["certainty_policy"],
                    body_json=json.dumps(item.get("body") or {}, ensure_ascii=True),
                    created_at=now,
                    updated_at=now,
                )
            )
        for item in DEFAULT_DATASET_CARDS:
            exists = session.execute(
                select(DatasetCard).where(DatasetCard.card_id == item["card_id"])
            ).scalar_one_or_none()
            if exists:
                continue
            session.add(
                DatasetCard(
                    card_id=item["card_id"],
                    dataset_id=item["dataset_id"],
                    title=item["title"],
                    version=item["version"],
                    summary=item["summary"],
                    provenance=item["provenance"],
                    languages=item["languages"],
                    body_json=json.dumps(item.get("body") or {}, ensure_ascii=True),
                    created_at=now,
                    updated_at=now,
                )
            )


def list_optional_features() -> list[dict[str, str]]:
    return [{"feature": key, "purpose": purpose} for key, purpose in OPTIONAL_FEATURES.items()]


def upsert_consent(
    *,
    subject_key: str,
    feature: str,
    granted: bool,
    user_id: int | None = None,
    purpose: str | None = None,
    policy_version: str = "1.0",
) -> dict[str, Any]:
    if feature not in OPTIONAL_FEATURES:
        raise ValueError(f"Unknown optional feature: {feature}")
    now = now_iso()
    with session_scope() as session:
        row = session.execute(
            select(ConsentRecord).where(
                ConsentRecord.subject_key == subject_key,
                ConsentRecord.feature == feature,
            )
        ).scalar_one_or_none()
        purpose_text = purpose or OPTIONAL_FEATURES[feature]
        if row is None:
            row = ConsentRecord(
                subject_key=subject_key,
                user_id=user_id,
                feature=feature,
                granted=granted,
                purpose=purpose_text,
                policy_version=policy_version,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
        else:
            row.granted = granted
            row.purpose = purpose_text
            row.policy_version = policy_version
            row.user_id = user_id if user_id is not None else row.user_id
            row.updated_at = now
        session.flush()
        return _consent_dict(row)


def list_consents(*, subject_key: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    with session_scope() as session:
        stmt = select(ConsentRecord).order_by(ConsentRecord.updated_at.desc()).limit(limit)
        if subject_key:
            stmt = select(ConsentRecord).where(ConsentRecord.subject_key == subject_key).order_by(
                ConsentRecord.updated_at.desc()
            )
        rows = session.execute(stmt).scalars().all()
        return [_consent_dict(row) for row in rows]


def list_risks(*, status: str | None = None) -> list[dict[str, Any]]:
    with session_scope() as session:
        stmt = select(RiskRegisterEntry).order_by(RiskRegisterEntry.risk_id.asc())
        if status:
            stmt = stmt.where(RiskRegisterEntry.status == status)
        return [_risk_dict(row) for row in session.execute(stmt).scalars().all()]


def update_risk(
    risk_id: str,
    *,
    status: str | None = None,
    mitigation: str | None = None,
    residual_risk: str | None = None,
    owner: str | None = None,
) -> dict[str, Any]:
    with session_scope() as session:
        row = session.execute(
            select(RiskRegisterEntry).where(RiskRegisterEntry.risk_id == risk_id)
        ).scalar_one_or_none()
        if row is None:
            raise ValueError(f"Unknown risk_id: {risk_id}")
        if status is not None:
            row.status = status
        if mitigation is not None:
            row.mitigation = mitigation
        if residual_risk is not None:
            row.residual_risk = residual_risk
        if owner is not None:
            row.owner = owner
        row.updated_at = now_iso()
        session.flush()
        return _risk_dict(row)


def list_model_cards() -> list[dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(select(ModelCard).order_by(ModelCard.card_id.asc())).scalars().all()
        return [_model_card_dict(row) for row in rows]


def list_dataset_cards() -> list[dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(select(DatasetCard).order_by(DatasetCard.card_id.asc())).scalars().all()
        return [_dataset_card_dict(row) for row in rows]


def list_controls() -> list[dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(
            select(GovernanceControl).order_by(GovernanceControl.control_id.asc())
        ).scalars().all()
        return [_control_dict(row) for row in rows]


def compliance_dashboard() -> dict[str, Any]:
    from .repositories import list_audit_logs

    risks = list_risks()
    controls = list_controls()
    open_risks = [r for r in risks if r["status"] == "open"]
    implemented = [c for c in controls if c["status"] == "implemented"]
    audits = list_audit_logs(limit=20)
    return {
        "risks_total": len(risks),
        "risks_open": len(open_risks),
        "controls_total": len(controls),
        "controls_implemented": len(implemented),
        "model_cards": len(list_model_cards()),
        "dataset_cards": len(list_dataset_cards()),
        "consent_features": list(OPTIONAL_FEATURES.keys()),
        "recent_audit": audits,
        "certainty_policy": "none",
    }
