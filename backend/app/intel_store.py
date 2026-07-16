"""Intel persistence, ingest orchestration, correlation, and reports."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from sqlalchemy import or_, select

from .core.config import get_settings
from .db.models import IncidentReport, IntelCampaign, IntelCorrelation, IntelItem, IntelSource
from .db.session import session_scope
from .repositories import now_iso
from .services.intel.connectors import (
    ALLOWED_SOURCE_CLASSES,
    assert_allowed_source_class,
    assert_egress_allowed,
    get_connector,
    normalize_webhook_payload,
)


def _source_to_dict(row: IntelSource, *, include_secrets: bool = False) -> dict:
    payload = {
        "id": row.id,
        "name": row.name,
        "source_class": row.source_class,
        "endpoint_url": row.endpoint_url,
        "egress_host": row.egress_host,
        "tos_reference": row.tos_reference,
        "license": row.license,
        "auth_type": row.auth_type,
        "config": json.loads(row.config_json or "{}"),
        "enabled": bool(row.enabled),
        "last_ingested_at": row.last_ingested_at,
        "created_by_user_id": row.created_by_user_id,
        "created_at": row.created_at,
        "compliance": {
            "allowed_source_class": row.source_class in ALLOWED_SOURCE_CLASSES,
            "tos_reference": row.tos_reference,
            "license": row.license,
            "egress_host": row.egress_host,
        },
    }
    if include_secrets and row.credentials_json:
        payload["credentials_configured"] = True
    else:
        payload["credentials_configured"] = bool(row.credentials_json)
    return payload


def _item_to_dict(row: IntelItem) -> dict:
    return {
        "id": row.id,
        "source_id": row.source_id,
        "external_id": row.external_id,
        "title": row.title,
        "summary": row.summary,
        "url": row.url,
        "published_at": row.published_at,
        "content_hash": row.content_hash,
        "handles": json.loads(row.handles_json or "[]"),
        "urls": json.loads(row.urls_json or "[]"),
        "campaign_id": row.campaign_id,
        "created_at": row.created_at,
    }


def create_intel_source(
    *,
    name: str,
    source_class: str,
    endpoint_url: str,
    tos_reference: str,
    license_name: str = "unknown",
    auth_type: str = "none",
    credentials: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    enabled: bool = True,
    created_by_user_id: int | None = None,
) -> dict:
    source_class = assert_allowed_source_class(source_class)
    tos_reference = (tos_reference or "").strip()
    if len(tos_reference) < 3:
        raise ValueError("tos_reference is required for compliance")
    if source_class == "partner_webhook":
        host = "webhook.local"
        endpoint = (endpoint_url or "webhook://partner").strip()
    else:
        endpoint = (endpoint_url or "").strip()
        host = assert_egress_allowed(endpoint)
    with session_scope() as session:
        row = IntelSource(
            name=name.strip(),
            source_class=source_class,
            endpoint_url=endpoint,
            egress_host=host,
            tos_reference=tos_reference,
            license=(license_name or "unknown").strip()[:255],
            auth_type=(auth_type or "none").strip()[:32],
            credentials_json=json.dumps(credentials or {}, ensure_ascii=True) if credentials else None,
            config_json=json.dumps(config or {}, ensure_ascii=True),
            enabled=bool(enabled),
            created_by_user_id=created_by_user_id,
            created_at=now_iso(),
        )
        session.add(row)
        session.flush()
        return _source_to_dict(row)


def list_intel_sources(*, enabled_only: bool = False) -> list[dict]:
    with session_scope() as session:
        rows = session.scalars(select(IntelSource).order_by(IntelSource.id.desc())).all()
        items = []
        for row in rows:
            if enabled_only and not row.enabled:
                continue
            items.append(_source_to_dict(row))
        return items


def get_intel_source(source_id: int) -> dict | None:
    with session_scope() as session:
        row = session.get(IntelSource, source_id)
        return _source_to_dict(row) if row else None


def set_intel_source_enabled(source_id: int, enabled: bool) -> dict:
    with session_scope() as session:
        row = session.get(IntelSource, source_id)
        if not row:
            raise ValueError("Source not found")
        row.enabled = bool(enabled)
        session.flush()
        return _source_to_dict(row)


def ingest_source(source_id: int) -> dict[str, Any]:
    settings = get_settings()
    if not settings.intel_enabled:
        raise ValueError("INTEL_ENABLED is false")
    with session_scope() as session:
        source = session.get(IntelSource, source_id)
        if not source:
            raise ValueError("Source not found")
        if not source.enabled:
            raise ValueError("Source is disabled")
        if source.source_class == "partner_webhook":
            raise ValueError("partner_webhook sources receive push data via /intel/webhook/{id}")
        connector = get_connector(source.source_class)
        config = json.loads(source.config_json or "{}")
        credentials = json.loads(source.credentials_json or "{}") if source.credentials_json else None
        fetched = connector.fetch(
            endpoint_url=source.endpoint_url,
            config=config,
            credentials=credentials,
        )
        created = 0
        skipped = 0
        for item in fetched:
            exists = session.scalar(
                select(IntelItem).where(
                    IntelItem.source_id == source.id,
                    IntelItem.external_id == item.external_id,
                )
            )
            if exists:
                skipped += 1
                continue
            session.add(
                IntelItem(
                    source_id=source.id,
                    external_id=item.external_id[:512],
                    title=item.title[:512],
                    summary=item.summary,
                    url=(item.url or None),
                    published_at=item.published_at,
                    content_hash=item.content_hash(),
                    handles_json=json.dumps(item.handles, ensure_ascii=True),
                    urls_json=json.dumps(item.urls, ensure_ascii=True),
                    raw_json=json.dumps(item.raw, ensure_ascii=True),
                    created_at=now_iso(),
                )
            )
            created += 1
        source.last_ingested_at = now_iso()
        session.flush()
        return {
            "source_id": source_id,
            "fetched": len(fetched),
            "created": created,
            "skipped": skipped,
            "ingested_at": source.last_ingested_at,
        }


def ingest_webhook(source_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    with session_scope() as session:
        source = session.get(IntelSource, source_id)
        if not source:
            raise ValueError("Source not found")
        if source.source_class != "partner_webhook":
            raise ValueError("Webhook ingest only allowed for partner_webhook sources")
        if not source.enabled:
            raise ValueError("Source is disabled")
        fetched = normalize_webhook_payload(payload)
        created = 0
        for item in fetched:
            exists = session.scalar(
                select(IntelItem).where(
                    IntelItem.source_id == source.id,
                    IntelItem.external_id == item.external_id,
                )
            )
            if exists:
                continue
            session.add(
                IntelItem(
                    source_id=source.id,
                    external_id=item.external_id[:512],
                    title=item.title[:512],
                    summary=item.summary,
                    url=item.url,
                    published_at=item.published_at,
                    content_hash=item.content_hash(),
                    handles_json=json.dumps(item.handles, ensure_ascii=True),
                    urls_json=json.dumps(item.urls, ensure_ascii=True),
                    raw_json=json.dumps(item.raw, ensure_ascii=True),
                    created_at=now_iso(),
                )
            )
            created += 1
        source.last_ingested_at = now_iso()
        session.flush()
        return {"source_id": source_id, "created": created, "fetched": len(fetched)}


def list_intel_items(*, source_id: int | None = None, q: str | None = None, limit: int = 50) -> list[dict]:
    safe_limit = max(1, min(limit, 200))
    with session_scope() as session:
        stmt = select(IntelItem).order_by(IntelItem.id.desc()).limit(safe_limit)
        filters = []
        if source_id is not None:
            filters.append(IntelItem.source_id == source_id)
        if q and q.strip():
            needle = f"%{q.strip().lower()}%"
            filters.append(or_(IntelItem.title.ilike(needle), IntelItem.summary.ilike(needle)))
        if filters:
            stmt = select(IntelItem).where(*filters).order_by(IntelItem.id.desc()).limit(safe_limit)
        return [_item_to_dict(row) for row in session.scalars(stmt).all()]


def correlate_intel(*, limit_items: int = 200) -> dict[str, Any]:
    """Correlate intel items to incidents via shared URLs/handles and cluster campaigns."""
    with session_scope() as session:
        items = session.scalars(select(IntelItem).order_by(IntelItem.id.desc()).limit(limit_items)).all()
        incidents = session.scalars(select(IncidentReport).order_by(IncidentReport.id.desc()).limit(300)).all()

        correlations_created = 0
        for item in items:
            handles = set(json.loads(item.handles_json or "[]"))
            urls = set(json.loads(item.urls_json or "[]"))
            title_l = (item.title or "").lower()
            for incident in incidents:
                blob = f"{incident.description} {incident.public_advisory or ''} {incident.decision_summary or ''}".lower()
                score = 0
                matched_handles = [h for h in handles if h.lower() in blob]
                matched_urls = [u for u in urls if u.lower() in blob]
                if matched_handles:
                    score += 40 + min(20, 5 * len(matched_handles))
                if matched_urls:
                    score += 45 + min(20, 5 * len(matched_urls))
                # light title token overlap
                tokens = [t for t in title_l.split() if len(t) > 4][:6]
                overlap = sum(1 for t in tokens if t in blob)
                if overlap >= 2:
                    score += 15
                if score < 40:
                    continue
                exists = session.scalar(
                    select(IntelCorrelation).where(
                        IntelCorrelation.intel_item_id == item.id,
                        IntelCorrelation.incident_id == incident.id,
                    )
                )
                if exists:
                    continue
                session.add(
                    IntelCorrelation(
                        intel_item_id=item.id,
                        incident_id=incident.id,
                        case_id=None,
                        correlation_type="url_handle_text",
                        score=min(100, score),
                        details_json=json.dumps(
                            {"handles": matched_handles, "urls": matched_urls, "token_overlap": overlap},
                            ensure_ascii=True,
                        ),
                        created_at=now_iso(),
                    )
                )
                correlations_created += 1

        # Campaign clustering by shared handle/url
        handle_map: dict[str, list[int]] = defaultdict(list)
        url_map: dict[str, list[int]] = defaultdict(list)
        item_by_id = {item.id: item for item in items}
        for item in items:
            for handle in json.loads(item.handles_json or "[]"):
                handle_map[handle.lower()].append(item.id)
            for url in json.loads(item.urls_json or "[]"):
                url_map[url.lower()].append(item.id)

        clusters: list[set[int]] = []
        seen: set[int] = set()
        for mapping in (handle_map, url_map):
            for key, ids in mapping.items():
                if len(ids) < 2:
                    continue
                cluster = set(ids)
                if cluster & seen and len(cluster) < 3:
                    continue
                clusters.append(cluster)
                seen |= cluster

        campaigns_created = 0
        for cluster in clusters[:20]:
            members = [item_by_id[i] for i in cluster if i in item_by_id]
            if len(members) < 2:
                continue
            shared_handles = sorted({h for m in members for h in json.loads(m.handles_json or "[]")})
            shared_urls = sorted({u for m in members for u in json.loads(m.urls_json or "[]")})
            name = f"Campaign signal ({len(members)} items)"
            stamp = now_iso()
            campaign = IntelCampaign(
                name=name,
                status="detected",
                signal_count=len(members),
                shared_handles_json=json.dumps(shared_handles[:20], ensure_ascii=True),
                shared_urls_json=json.dumps(shared_urls[:20], ensure_ascii=True),
                summary=f"Coordinated indicators across {len(members)} intel items.",
                created_at=stamp,
                updated_at=stamp,
            )
            session.add(campaign)
            session.flush()
            for member in members:
                member.campaign_id = campaign.id
            campaigns_created += 1

        session.flush()
        return {
            "correlations_created": correlations_created,
            "campaigns_created": campaigns_created,
            "items_scanned": len(items),
            "incidents_scanned": len(incidents),
        }


def list_campaigns(limit: int = 50) -> list[dict]:
    with session_scope() as session:
        rows = session.scalars(select(IntelCampaign).order_by(IntelCampaign.id.desc()).limit(limit)).all()
        return [
            {
                "id": row.id,
                "name": row.name,
                "status": row.status,
                "signal_count": row.signal_count,
                "shared_handles": json.loads(row.shared_handles_json or "[]"),
                "shared_urls": json.loads(row.shared_urls_json or "[]"),
                "summary": row.summary,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
            for row in rows
        ]


def list_correlations(limit: int = 50) -> list[dict]:
    with session_scope() as session:
        rows = session.scalars(select(IntelCorrelation).order_by(IntelCorrelation.id.desc()).limit(limit)).all()
        return [
            {
                "id": row.id,
                "intel_item_id": row.intel_item_id,
                "incident_id": row.incident_id,
                "case_id": row.case_id,
                "correlation_type": row.correlation_type,
                "score": row.score,
                "details": json.loads(row.details_json or "{}"),
                "created_at": row.created_at,
            }
            for row in rows
        ]


def build_national_intel_report() -> dict[str, Any]:
    sources = list_intel_sources()
    items = list_intel_items(limit=100)
    campaigns = list_campaigns(limit=50)
    correlations = list_correlations(limit=100)
    report = {
        "report_type": "national_threat_intelligence",
        "generated_at": now_iso(),
        "compliance_note": (
            "Sources are restricted to official APIs, RSS/Atom, open data, and partner webhooks. "
            "ToS-violating scraping is forbidden."
        ),
        "summary": {
            "sources": len(sources),
            "enabled_sources": sum(1 for s in sources if s["enabled"]),
            "items": len(items),
            "campaigns": len(campaigns),
            "correlations": len(correlations),
        },
        "sources": sources,
        "recent_items": items[:25],
        "campaigns": campaigns[:20],
        "correlations": correlations[:30],
    }
    report["markdown"] = _report_markdown(report)
    return report


def _report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MboaShield National Threat Intelligence Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        report["compliance_note"],
        "",
        "## Summary",
        f"- Sources: {report['summary']['sources']} (enabled {report['summary']['enabled_sources']})",
        f"- Items: {report['summary']['items']}",
        f"- Campaigns: {report['summary']['campaigns']}",
        f"- Correlations: {report['summary']['correlations']}",
        "",
        "## Campaigns",
    ]
    for campaign in report["campaigns"]:
        lines.append(f"- **{campaign['name']}** ({campaign['signal_count']} signals): {campaign.get('summary') or ''}")
    lines.extend(["", "## Recent intel"])
    for item in report["recent_items"]:
        lines.append(f"- {item['title']} ({item.get('url') or 'no-url'})")
    lines.extend(["", "## Correlations"])
    for corr in report["correlations"]:
        lines.append(
            f"- Intel #{corr['intel_item_id']} ? Incident #{corr['incident_id']} score={corr['score']}"
        )
    return "\n".join(lines)
