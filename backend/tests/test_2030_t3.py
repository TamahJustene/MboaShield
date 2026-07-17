"""MboaShield 2030 transformation phase T3 tests."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_health_reports_t3(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "2.8.0"
    assert health["transformation_phase"] == "CI-1"


def test_portal_shell_and_developer_static(client):
    test_client, _ = client
    shell = test_client.get("/static/portal-shell.js")
    assert shell.status_code == 200
    assert b"MboaShieldPortal" in shell.content

    developer = test_client.get("/static/developer.html")
    assert developer.status_code == 200
    assert b"portal-shell" in developer.content
    assert b"Developer portal" in developer.content

    for page in ("analyst.html", "ntoc.html", "institution-portal.html"):
        res = test_client.get(f"/static/{page}")
        assert res.status_code == 200
        assert b'id="portal-shell"' in res.content
        assert b"portal-shell.js" in res.content


def test_portal_shell_file_on_disk():
    path = ROOT / "frontend" / "static" / "portal-shell.js"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "getLang" in text
    assert "authHeaders" in text
