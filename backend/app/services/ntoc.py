"""National Trust Operations Center aggregations."""

from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy import select

from ..core.config import get_settings
from ..db.models import IncidentReport, Institution, VerificationCheck
from ..db.session import session_scope
from ..repositories import incident_status_counts, now_iso
from ..services.analytics import CAMEROON_REGIONS, build_national_analytics
from ..ntoc_store import save_institution_health_snapshots, search_cases


def compute_threat_level(analytics: dict[str, Any] | None = None) -> dict[str, Any]:
    settings = get_settings()
    data = analytics or build_national_analytics()
    overview = data.get("overview") or {}
    bands = (data.get("threat_trends") or {}).get("by_risk_band") or {}
    high = int(bands.get("high") or 0)
    medium = int(bands.get("medium") or 0)
    open_incidents = int(overview.get("open_queue") or 0)
    total_checks = max(1, int(overview.get("checks_total") or 1))
    high_share = (high / total_checks) * 100.0
    pressure = min(100, int(round(0.55 * high_share + 0.35 * min(open_incidents * 8, 100) + 0.10 * medium)))
    if pressure >= settings.threat_critical:
        level = "critical"
    elif pressure >= settings.threat_high:
        level = "high"
    elif pressure >= settings.threat_elevated:
        level = "elevated"
    else:
        level = "normal"
    return {
        "level": level,
        "score": pressure,
        "thresholds": {
            "elevated": settings.threat_elevated,
            "high": settings.threat_high,
            "critical": settings.threat_critical,
        },
        "drivers": {
            "high_risk_checks": high,
            "medium_risk_checks": medium,
            "open_queue": open_incidents,
        },
        "generated_at": now_iso(),
    }


def build_regional_map(analytics: dict[str, Any] | None = None) -> dict[str, Any]:
    data = analytics or build_national_analytics()
    regions = data.get("regional_heat_map") or []
    items = []
    for row in regions:
        name = row.get("region") or "Unspecified"
        count = int(row.get("incident_count") or 0)
        intensity_raw = row.get("intensity")
        intensity = int(round(float(intensity_raw) * 100)) if intensity_raw is not None else min(100, count * 12)
        items.append({"region": name, "incident_count": count, "intensity": intensity})
    known = {item["region"] for item in items}
    for region in CAMEROON_REGIONS:
        if region not in known:
            items.append({"region": region, "incident_count": 0, "intensity": 0})
    items.sort(key=lambda item: (-item["incident_count"], item["region"]))
    return {"regions": items, "count": len(items), "map_mode": "offline_regions"}


def compute_institution_health() -> list[dict[str, Any]]:
    open_statuses = {
        "open",
        "ai_analysis",
        "analyst_review",
        "reviewing",
        "institution_review",
        "decision",
        "public_advisory",
    }
    with session_scope() as session:
        institutions = session.scalars(select(Institution)).all()
        incidents = session.scalars(select(IncidentReport)).all()
        checks = session.scalars(select(VerificationCheck).order_by(VerificationCheck.id.desc()).limit(500)).all()

        open_by_inst: Counter[str] = Counter()
        for incident in incidents:
            if incident.institution_id and incident.status in open_statuses:
                open_by_inst[incident.institution_id] += 1

        high_by_inst: Counter[str] = Counter()
        for check in checks:
            if (check.risk_score or 0) < 70:
                continue
            try:
                import json

                result = json.loads(check.result_json or "{}")
            except Exception:
                result = {}
            matched = result.get("matched_institution") or {}
            inst_id = matched.get("id")
            if inst_id:
                high_by_inst[str(inst_id)] += 1

        items = []
        for inst in institutions:
            open_count = open_by_inst.get(inst.id, 0)
            high_count = high_by_inst.get(inst.id, 0)
            score = max(0, 100 - open_count * 12 - high_count * 8)
            items.append(
                {
                    "institution_id": inst.id,
                    "name": inst.name,
                    "short_name": inst.short_name,
                    "health_score": score,
                    "open_incidents": open_count,
                    "high_risk_checks": high_count,
                    "details": {"verified": bool(inst.verified)},
                }
            )
        items.sort(key=lambda item: item["health_score"])
        save_institution_health_snapshots(items)
        return items


def build_ntoc_dashboard() -> dict[str, Any]:
    settings = get_settings()
    if not settings.ntoc_enabled:
        return {"enabled": False, "message": "NTOC is disabled"}
    analytics = build_national_analytics()
    threat = compute_threat_level(analytics)
    regional = build_regional_map(analytics)
    cases = search_cases(limit=20)
    open_cases = [item for item in cases if item["status"] != "closed"]
    health = compute_institution_health()
    status_counts = incident_status_counts()
    return {
        "enabled": True,
        "generated_at": now_iso(),
        "threat_level": threat,
        "regional_map": regional,
        "queue": {
            "status_counts": status_counts,
            "active_total": sum(
                status_counts.get(key, 0)
                for key in ("open", "ai_analysis", "analyst_review", "reviewing", "institution_review", "decision")
            ),
        },
        "cases": {"recent": cases[:10], "open_count": len(open_cases), "total_listed": len(cases)},
        "institution_health": health[:12],
        "analytics_overview": analytics.get("overview") or {},
        "links": {
            "investigation": "/static/investigation.html",
            "analyst": "/static/analyst.html",
            "national": "/static/national.html",
        },
    }


def build_investigation_workspace(case_id: int) -> dict[str, Any]:
    from ..ntoc_store import (
        evidence_for_case,
        get_case,
        list_case_assignments,
        list_case_notes,
    )
    from ..repositories import list_incident_events

    case = get_case(case_id)
    if not case:
        raise ValueError("Case not found")
    evidence = evidence_for_case(case_id)
    timeline = []
    if case.get("incident_id"):
        timeline = list_incident_events(case["incident_id"])
    return {
        "case": case,
        "notes": list_case_notes(case_id),
        "assignments": list_case_assignments(case_id),
        "timeline": timeline,
        "evidence": evidence,
        "generated_at": now_iso(),
    }
