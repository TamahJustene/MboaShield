"""Phase T1 trust assessment persistence."""

from __future__ import annotations

import json

from sqlalchemy import select

from .db.models import TrustAssessment
from .db.session import session_scope
from .repositories import now_iso


def save_trust_assessment(
    *,
    object_type: str,
    object_id: str | None,
    score: int,
    band: str,
    certainty: str,
    signals: list[dict],
    evidence_refs: list[dict],
    verification_check_id: int | None,
    payload: dict,
    lang: str = "en",
    user_id: int | None = None,
) -> int:
    stamp = now_iso()
    with session_scope() as session:
        row = TrustAssessment(
            object_type=object_type,
            object_id=object_id,
            score=score,
            band=band,
            certainty=certainty,
            signals_json=json.dumps(signals, ensure_ascii=True),
            evidence_refs_json=json.dumps(evidence_refs, ensure_ascii=True),
            verification_check_id=verification_check_id,
            payload_json=json.dumps(payload, ensure_ascii=True),
            input_lang=lang,
            user_id=user_id,
            created_at=stamp,
        )
        session.add(row)
        session.flush()
        return int(row.id)


def get_trust_assessment(assessment_id: int) -> dict | None:
    with session_scope() as session:
        row = session.get(TrustAssessment, assessment_id)
        if not row:
            return None
        return _row_to_assessment(row)


def list_recent_trust_assessments(limit: int = 20, object_type: str | None = None) -> list[dict]:
    safe_limit = max(1, min(limit, 100))
    with session_scope() as session:
        stmt = select(TrustAssessment).order_by(TrustAssessment.id.desc()).limit(safe_limit)
        if object_type:
            stmt = (
                select(TrustAssessment)
                .where(TrustAssessment.object_type == object_type)
                .order_by(TrustAssessment.id.desc())
                .limit(safe_limit)
            )
        rows = session.scalars(stmt).all()
        return [_row_to_assessment(row) for row in rows]


def _row_to_assessment(row: TrustAssessment) -> dict:
    return {
        "id": row.id,
        "object_type": row.object_type,
        "object_id": row.object_id,
        "score": row.score,
        "band": row.band,
        "certainty": row.certainty,
        "signals": json.loads(row.signals_json or "[]"),
        "evidence_refs": json.loads(row.evidence_refs_json or "[]"),
        "verification_check_id": row.verification_check_id,
        "lang": row.input_lang,
        "user_id": row.user_id,
        "created_at": row.created_at,
        "payload": json.loads(row.payload_json or "{}"),
    }
