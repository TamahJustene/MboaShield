"""MboaShield 2030 transformation phase T5 tests."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_health_reports_t5(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "2.7.0"
    assert health["transformation_phase"] == "T7"
    assert health["scim_read_only"] is True


def test_zero_trust_checklist_on_security_status(client):
    test_client, _ = client
    body = test_client.get("/api/v1/auth/security-status").json()
    assert "zero_trust" in body
    zt = body["zero_trust"]
    assert zt["checks"]["scim_read_available"] is True
    assert zt["checks"]["rls_sql_template_shipped"] is True
    assert zt["checks"]["kms_guide_shipped"] is True
    assert body["scim"]["users"] == "/scim/v2/Users"


def test_scim_service_provider_and_users(client):
    test_client, _ = client
    cfg = test_client.get("/scim/v2/ServiceProviderConfig")
    assert cfg.status_code == 200
    assert cfg.json()["x_mboashield"]["mode"] == "read_only_stub"

    users = test_client.get("/scim/v2/Users")
    assert users.status_code == 200
    payload = users.json()
    assert payload["schemas"] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    assert "Resources" in payload

    create = test_client.post("/scim/v2/Users", json={})
    assert create.status_code == 501


def test_national_profile_and_docs_exist():
    assert (ROOT / "deploy" / "profiles" / "national.env").is_file()
    assert (ROOT / "deploy" / "sql" / "rls_tenant.sql").is_file()
    assert (ROOT / "docs" / "manuals" / "KMS_AND_SECRETS.md").is_file()
    assert (ROOT / "docs" / "adr" / "0006-zero-trust-national-identity.md").is_file()
