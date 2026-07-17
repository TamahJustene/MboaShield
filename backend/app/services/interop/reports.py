"""National report CSV exports (T4)."""

from __future__ import annotations

import csv
import io
from typing import Any

from ...repositories import list_incident_reports, now_iso


def incidents_csv(*, limit: int = 200, status: str | None = None) -> str:
    rows = list_incident_reports(limit=limit, status=status)
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=[
            "id",
            "report_type",
            "status",
            "priority",
            "region",
            "institution_id",
            "verification_check_id",
            "created_at",
            "updated_at",
        ],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "id": row.get("id"),
                "report_type": row.get("report_type"),
                "status": row.get("status"),
                "priority": row.get("priority"),
                "region": row.get("region"),
                "institution_id": row.get("institution_id"),
                "verification_check_id": row.get("verification_check_id"),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
            }
        )
    return buf.getvalue()


def incidents_csv_meta(*, limit: int = 200, status: str | None = None) -> dict[str, Any]:
    return {
        "format": "csv",
        "generated_at": now_iso(),
        "limit": limit,
        "status_filter": status,
        "csv": incidents_csv(limit=limit, status=status),
    }
