"""MboaShield 2030 continuous improvement CI-1 tests."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_health_reports_ci1(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "2.8.0"
    assert health["transformation_phase"] == "CI-1"
    assert health["taxii_read_only"] is True


def test_taxii_discovery_and_objects(client):
    test_client, _ = client
    discovery = test_client.get("/taxii2/")
    assert discovery.status_code == 200
    assert "api_roots" in discovery.json()

    collections = test_client.get("/taxii2/collections/")
    assert collections.status_code == 200
    assert collections.json()["collections"][0]["can_read"] is True

    objects = test_client.get("/taxii2/collections/mboashield-intel/objects/?limit=5")
    assert objects.status_code == 200
    body = objects.json()
    assert "objects" in body


def test_scim_create_user(client):
    test_client, _ = client
    res = test_client.post(
        "/scim/v2/Users",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "scim.ci1@example.cm",
            "displayName": "SCIM CI1",
            "roles": [{"value": "analyst"}],
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["userName"] == "scim.ci1@example.cm"
    assert body["roles"][0]["value"] == "analyst"
    ext = body["urn:ietf:params:scim:schemas:extension:mboashield:2.0:User"]
    assert ext.get("temporary_password")


def test_migrated_portals_use_shell(client):
    test_client, _ = client
    for page in ("intel.html", "investigation.html", "national.html"):
        res = test_client.get(f"/static/{page}")
        assert res.status_code == 200
        assert b'id="portal-shell"' in res.content
        assert b"portal-shell.js" in res.content
    assert (ROOT / "docs" / "PHASE_CI1_PLAN.md").is_file()
