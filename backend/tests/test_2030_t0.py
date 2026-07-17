"""MboaShield 2030 transformation phase T0 tests."""

from __future__ import annotations

from backend.app.core.openapi_pillars import PILLAR_CATALOG, PROGRAM_ID, TRANSFORMATION_PHASE


def test_health_reports_2030_t0(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "2.7.0"
    assert health["program"] == PROGRAM_ID
    assert health["transformation_phase"] == TRANSFORMATION_PHASE
    assert health["country_pack"] == "cm"


def test_program_endpoint(client):
    test_client, _ = client
    res = test_client.get("/api/v1/program")
    assert res.status_code == 200
    body = res.json()
    assert body["program"] == PROGRAM_ID
    assert body["transformation_phase"] == "T7"
    assert len(body["pillars"]) == len(PILLAR_CATALOG)
    assert body["country_pack"] == "cm"


def test_openapi_pillar_tags():
    from backend.app.main import create_app

    app = create_app()
    schema = app.openapi()
    tag_names = {t["name"] for t in schema.get("tags", [])}
    for pillar in PILLAR_CATALOG:
        assert pillar["id"] in tag_names
    assert schema["info"].get("x-mboashield-program") == PROGRAM_ID
    assert schema["info"].get("x-transformation-phase") == TRANSFORMATION_PHASE
