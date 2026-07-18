"""MboaShield 2030 transformation phase T7 tests."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_health_reports_t7(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "2.8.0"
    assert health["transformation_phase"] == "CI-1"


def test_country_pack_and_sectors(client):
    test_client, _ = client
    pack = test_client.get("/api/v1/country-pack").json()
    assert pack["pack"]["iso_country"] == "CM"
    assert "legal" in pack["pack"]
    assert any(item["pack_id"] == "cm" for item in pack["available_packs"])

    sectors = test_client.get("/api/v1/sectors").json()
    assert "election" in sectors["enabled_ids"]
    assert "health" in sectors["enabled_ids"]
    assert "finance" in sectors["enabled_ids"]

    program = test_client.get("/api/v1/program").json()
    assert program["sectors_enabled"]


def test_governance_framework_map(client):
    test_client, _ = client
    res = test_client.get("/api/v1/governance/framework-map")
    assert res.status_code == 200
    body = res.json()
    assert "iso27001" in body["frameworks_supported"]
    assert body["count"] >= 1
    assert body["controls"][0]["frameworks"]["iso27001"]


def test_sector_ui_and_packs_on_disk():
    assert (ROOT / "frontend" / "static" / "sectors.html").is_file()
    assert (ROOT / "deploy" / "country-packs" / "cm" / "pack.json").is_file()
    assert (ROOT / "deploy" / "country-packs" / "template" / "pack.json").is_file()
    assert (ROOT / "docs" / "adr" / "0008-country-packs-and-sectors.md").is_file()
    assert "COPY deploy deploy" in (ROOT / "Dockerfile").read_text(encoding="utf-8")


def test_country_pack_has_safe_builtin_fallback(monkeypatch, tmp_path):
    from backend.app.services import country_pack

    country_pack._read_pack_file.cache_clear()
    monkeypatch.setattr(country_pack, "PACKS_ROOT", tmp_path / "missing")
    pack = country_pack.load_country_pack("cm")
    assert pack["iso_country"] == "CM"
    assert pack["default_sectors"] == ["election", "health", "finance"]
    country_pack._read_pack_file.cache_clear()
