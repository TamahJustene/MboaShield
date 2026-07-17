"""Phase 15 documentation suite tests."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


REQUIRED_MANUALS = [
    "README.md",
    "USER.md",
    "ADMINISTRATOR.md",
    "DEVELOPER.md",
    "OPERATIONS.md",
    "SECURITY.md",
    "DEPLOYMENT.md",
    "MAINTENANCE.md",
    "API_REFERENCE.md",
    "ARCHITECTURE_GUIDE.md",
    "AI_GOVERNANCE.md",
]


def test_manuals_exist():
    manuals = ROOT / "docs" / "manuals"
    assert manuals.is_dir()
    for name in REQUIRED_MANUALS:
        path = manuals / name
        assert path.is_file(), f"missing {name}"
        assert path.stat().st_size > 100


def test_openapi_export_schema(tmp_path):
    from backend.app.main import create_app

    app = create_app()
    schema = app.openapi()
    assert schema["info"]["version"] == "2.8.0"
    assert len(schema["paths"]) >= 20
    assert any(p.startswith("/api/v1") for p in schema["paths"])

    out = tmp_path / "openapi.json"
    out.write_text(json.dumps(schema), encoding="utf-8")
    assert out.stat().st_size > 1000


def test_health_reports_phase15(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "2.8.0"
