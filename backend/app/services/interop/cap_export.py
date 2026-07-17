"""CAP 1.2 advisory export from public_advisory incidents (T4)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any
from xml.dom import minidom

from ...repositories import get_incident_report, list_incident_reports, now_iso


def _text(parent: ET.Element, tag: str, value: str) -> None:
    el = ET.SubElement(parent, tag)
    el.text = value


def build_cap_alert(incident: dict[str, Any]) -> str:
    settings_tenant = "CM"
    alert = ET.Element("alert")
    alert.set("xmlns", "urn:oasis:names:tc:emergency:cap:1.2")
    _text(alert, "identifier", f"mboashield-incident-{incident['id']}")
    _text(alert, "sender", "mboashield@national.cm")
    _text(alert, "sent", incident.get("updated_at") or incident.get("created_at") or now_iso())
    _text(alert, "status", "Actual")
    _text(alert, "msgType", "Alert")
    _text(alert, "scope", "Public")
    info = ET.SubElement(alert, "info")
    _text(info, "category", "Security")
    _text(info, "event", "Digital trust public advisory")
    _text(info, "urgency", "Expected")
    _text(info, "severity", "Moderate" if (incident.get("priority") or "medium") != "high" else "Severe")
    _text(info, "certainty", "Unknown")
    _text(info, "senderName", "MboaShield National Trust Platform")
    _text(info, "headline", f"Incident #{incident['id']} public advisory")
    _text(info, "description", incident.get("public_advisory") or incident.get("description") or "")
    _text(info, "instruction", "Verify information with official sources before sharing.")
    area = ET.SubElement(info, "area")
    _text(area, "areaDesc", incident.get("region") or settings_tenant)
    rough = ET.tostring(alert, encoding="utf-8")
    return minidom.parseString(rough).toprettyxml(indent="  ")


def export_cap_for_incident(incident_id: int) -> str:
    incident = get_incident_report(incident_id)
    if not incident:
        raise ValueError("Incident not found")
    if incident.get("status") != "public_advisory" and not incident.get("public_advisory"):
        raise ValueError("Incident has no public advisory content")
    return build_cap_alert(incident)


def export_cap_bundle(*, limit: int = 20) -> dict[str, Any]:
    reports = list_incident_reports(limit=limit, status="public_advisory")
    # also include any with advisory text
    extras = [
        item
        for item in list_incident_reports(limit=limit)
        if item.get("public_advisory") and item["id"] not in {r["id"] for r in reports}
    ]
    items = reports + extras
    return {
        "count": len(items),
        "generated_at": now_iso(),
        "format": "CAP-1.2",
        "alerts": [{"incident_id": item["id"], "xml": build_cap_alert(item)} for item in items],
    }
