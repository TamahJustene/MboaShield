"""National analytics aggregation for government situational awareness."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from ..db.models import (
    AnalysisFeedback,
    IncidentEvent,
    IncidentReport,
    LessonCertificate,
    User,
    VerificationCheck,
)
from ..db.session import session_scope
from ..repositories import now_iso

CAMEROON_REGIONS = [
    "Adamawa",
    "Centre",
    "East",
    "Far North",
    "Littoral",
    "North",
    "Northwest",
    "South",
    "Southwest",
    "West",
    "Unspecified",
]


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _day_key(value: str | None) -> str:
    dt = _parse_dt(value)
    if not dt:
        return "unknown"
    return dt.date().isoformat()


def _load_result(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _normalize_region(region: str | None) -> str:
    value = (region or "").strip()
    if not value:
        return "Unspecified"
    for known in CAMEROON_REGIONS:
        if value.lower() == known.lower():
            return known
    return value.title()


def record_analysis_feedback(
    *,
    check_id: int,
    label: str,
    note: str | None = None,
    actor_user_id: int | None = None,
) -> dict[str, Any]:
    allowed = {"true_positive", "false_positive", "true_negative", "false_negative"}
    label = (label or "").strip().lower()
    if label not in allowed:
        raise ValueError(f"Invalid label. Allowed: {', '.join(sorted(allowed))}")
    with session_scope() as session:
        check = session.get(VerificationCheck, check_id)
        if not check:
            raise ValueError("verification check not found")
        row = AnalysisFeedback(
            verification_check_id=check_id,
            label=label,
            note=(note or "").strip() or None,
            actor_user_id=actor_user_id,
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        return {
            "id": row.id,
            "verification_check_id": row.verification_check_id,
            "label": row.label,
            "note": row.note,
            "actor_user_id": row.actor_user_id,
            "created_at": row.created_at,
        }


def build_national_analytics(limit_checks: int = 500, limit_incidents: int = 500) -> dict[str, Any]:
    with session_scope() as session:
        checks = session.scalars(
            select(VerificationCheck).order_by(VerificationCheck.id.desc()).limit(limit_checks)
        ).all()
        incidents = session.scalars(
            select(IncidentReport).order_by(IncidentReport.id.desc()).limit(limit_incidents)
        ).all()
        events = session.scalars(select(IncidentEvent).order_by(IncidentEvent.id.asc())).all()
        users = session.scalars(select(User)).all()
        certificates = session.scalars(select(LessonCertificate)).all()
        feedback = session.scalars(select(AnalysisFeedback)).all()

        check_type_counts = Counter(item.check_type for item in checks)
        risk_band_counts = Counter((item.risk_band or "unknown") for item in checks)
        threat_counts: Counter[str] = Counter()
        deepfake_by_day: Counter[str] = Counter()
        checks_by_day: Counter[str] = Counter()
        institution_hits: Counter[str] = Counter()

        for check in checks:
            checks_by_day[_day_key(check.created_at)] += 1
            result = _load_result(check.result_json)
            analysis = result.get("ai_analysis") or {}
            for threat in analysis.get("threat_categories") or []:
                threat_counts[str(threat)] += 1
            if check.check_type in {"media", "audio"} and (check.risk_score or 0) >= 40:
                deepfake_by_day[_day_key(check.created_at)] += 1
            matched = result.get("matched_institution") or {}
            if matched.get("short_name"):
                institution_hits[str(matched["short_name"])] += 1
            elif check.check_type == "impersonation" and (check.risk_score or 0) >= 40:
                institution_hits["Unmatched spoof"] += 1

        region_counts = Counter(_normalize_region(item.region) for item in incidents)
        for region in CAMEROON_REGIONS:
            region_counts.setdefault(region, 0)

        status_counts = Counter(item.status for item in incidents)
        incident_by_day = Counter(_day_key(item.created_at) for item in incidents)

        # Response time: first event -> resolved/archived/dismissed
        terminal = {"resolved", "archived", "dismissed"}
        events_by_incident: dict[int, list[IncidentEvent]] = defaultdict(list)
        for event in events:
            events_by_incident[event.incident_id].append(event)

        response_hours: list[float] = []
        for incident in incidents:
            if incident.status not in terminal:
                continue
            timeline = events_by_incident.get(incident.id) or []
            start = _parse_dt(incident.created_at)
            end = _parse_dt(incident.updated_at)
            for event in timeline:
                if event.to_status in terminal:
                    end = _parse_dt(event.created_at) or end
                    break
            if start and end and end >= start:
                response_hours.append((end - start).total_seconds() / 3600.0)

        avg_response = round(sum(response_hours) / len(response_hours), 2) if response_hours else None
        median_response = None
        if response_hours:
            ordered = sorted(response_hours)
            mid = len(ordered) // 2
            median_response = round(
                ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2,
                2,
            )

        feedback_counts = Counter(item.label for item in feedback)
        labeled = sum(feedback_counts.values())
        tp = feedback_counts.get("true_positive", 0)
        tn = feedback_counts.get("true_negative", 0)
        fp = feedback_counts.get("false_positive", 0)
        fn = feedback_counts.get("false_negative", 0)
        accuracy = None
        precision = None
        false_positive_rate = None
        if labeled:
            accuracy = round((tp + tn) / labeled, 3)
            if (tp + fp) > 0:
                precision = round(tp / (tp + fp), 3)
            if (fp + tn) > 0:
                false_positive_rate = round(fp / (fp + tn), 3)

        # Disposition proxy when feedback is sparse
        resolved_like = status_counts.get("resolved", 0) + status_counts.get("archived", 0)
        dismissed = status_counts.get("dismissed", 0)
        disposition_total = resolved_like + dismissed
        disposition_proxy = None
        if disposition_total:
            disposition_proxy = {
                "confirmed_or_closed_ratio": round(resolved_like / disposition_total, 3),
                "dismissed_ratio": round(dismissed / disposition_total, 3),
                "sample_size": disposition_total,
            }

        checks_with_user = sum(1 for item in checks if item.user_id is not None)
        incidents_with_user = sum(1 for item in incidents if item.user_id is not None)

        heat_map = [
            {
                "region": region,
                "incident_count": int(region_counts.get(region, 0)),
                "intensity": min(1.0, float(region_counts.get(region, 0)) / 10.0),
            }
            for region in sorted(region_counts.keys(), key=lambda key: (-region_counts[key], key))
        ]

        return {
            "generated_at": now_iso(),
            "overview": {
                "checks_total": len(checks),
                "incidents_total": len(incidents),
                "users_total": len(users),
                "certificates_total": len(certificates),
                "feedback_total": labeled,
                "open_queue": sum(
                    status_counts.get(key, 0)
                    for key in (
                        "open",
                        "ai_analysis",
                        "analyst_review",
                        "reviewing",
                        "institution_review",
                        "decision",
                    )
                ),
            },
            "threat_trends": {
                "by_check_type": dict(check_type_counts),
                "by_risk_band": dict(risk_band_counts),
                "by_threat_category": dict(threat_counts),
                "checks_by_day": dict(sorted(checks_by_day.items())),
            },
            "deepfake_trends": {
                "high_risk_media_audio_by_day": dict(sorted(deepfake_by_day.items())),
                "media_checks": check_type_counts.get("media", 0),
                "audio_checks": check_type_counts.get("audio", 0),
            },
            "institution_attacks": {
                "top_targets": [
                    {"institution": name, "count": count}
                    for name, count in institution_hits.most_common(10)
                ],
                "impersonation_checks": check_type_counts.get("impersonation", 0),
            },
            "regional_heat_map": heat_map,
            "incident_timeline": {
                "by_day": dict(sorted(incident_by_day.items())),
                "by_status": dict(status_counts),
            },
            "response_time": {
                "sample_size": len(response_hours),
                "average_hours": avg_response,
                "median_hours": median_response,
                "unit": "hours",
            },
            "ai_accuracy": {
                "labeled_feedback": dict(feedback_counts),
                "accuracy": accuracy,
                "precision": precision,
                "false_positive_rate": false_positive_rate,
                "disposition_proxy": disposition_proxy,
                "honesty_note": (
                    "Accuracy metrics require analyst feedback labels. "
                    "Disposition ratios are operational proxies, not ground-truth model accuracy."
                ),
            },
            "citizen_participation": {
                "users_total": len(users),
                "checks_linked_to_users": checks_with_user,
                "incidents_linked_to_users": incidents_with_user,
                "certificates_issued": len(certificates),
                "participation_rate_checks": round(checks_with_user / max(len(checks), 1), 3),
            },
        }
