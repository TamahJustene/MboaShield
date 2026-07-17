"""Phase 10 Institution Administration Portal tests."""

from __future__ import annotations


def test_institution_portal_domains_memberships_branding_keys(client):
    test_client, _ = client

    # Use a seeded institution id from seed data, or create one
    created = test_client.post(
        "/api/v1/institutions",
        json={
            "id": "portal-demo",
            "name": "Portal Demo Ministry",
            "short_name": "PortalDemo",
            "url": "https://portal-demo.cm",
            "handles": ["@PortalDemo"],
            "verified": True,
        },
    )
    assert created.status_code == 200, created.text
    institution_id = created.json()["id"]

    overview = test_client.get(f"/api/v1/institution-portal/{institution_id}/overview")
    assert overview.status_code == 200
    assert overview.json()["institution"]["id"] == institution_id

    domain = test_client.post(
        f"/api/v1/institution-portal/{institution_id}/domains",
        json={"domain": "portal-demo.cm", "verification_method": "token_confirm"},
    )
    assert domain.status_code == 200, domain.text
    domain_body = domain.json()
    domain_id = domain_body["id"]
    token = domain_body["verification_token"]

    verified = test_client.post(
        f"/api/v1/institution-portal/{institution_id}/domains/{domain_id}/verify",
        json={"token": token},
    )
    assert verified.status_code == 200
    assert verified.json()["verified"] is True

    user = test_client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Inst Admin",
            "email": "inst-admin@portal-demo.cm",
            "password": "SecurePass1!",
        },
    )
    assert user.status_code == 200
    user_id = user.json()["user"]["id"]

    membership = test_client.post(
        f"/api/v1/institution-portal/{institution_id}/memberships",
        json={"user_id": user_id, "member_role": "admin"},
    )
    assert membership.status_code == 200, membership.text
    assert membership.json()["member_role"] == "admin"

    branding = test_client.put(
        f"/api/v1/institution-portal/{institution_id}/branding",
        json={
            "branding": {"primary_color": "#0b3d2e", "logo_url": "https://portal-demo.cm/logo.png"},
            "contact_email": "trust@portal-demo.cm",
        },
    )
    assert branding.status_code == 200
    assert branding.json()["branding"]["primary_color"] == "#0b3d2e"
    assert branding.json()["contact_email"] == "trust@portal-demo.cm"

    account = test_client.post(
        f"/api/v1/institution-portal/{institution_id}/official-accounts",
        json={"platform": "twitter", "handle": "PortalDemo", "url": "https://x.com/PortalDemo"},
    )
    assert account.status_code == 200
    assert account.json()["handle"] == "@PortalDemo"

    key = test_client.post(
        f"/api/v1/institution-portal/{institution_id}/api-keys",
        json={"name": "Integration key", "scopes": ["checks:create", "institutions:read"]},
    )
    assert key.status_code == 200, key.text
    raw = key.json()["api_key"]
    assert raw.startswith("msi_")

    me = test_client.get("/api/v1/partners/me", headers={"X-API-Key": raw})
    assert me.status_code == 200
    assert me.json()["institution_id"] == institution_id
    assert me.json()["key_type"] == "institution"

    case = test_client.post(
        "/api/v1/cases",
        json={
            "title": "Institution case",
            "summary": "Scoped investigation",
            "institution_id": institution_id,
            "priority": "high",
        },
    )
    assert case.status_code == 200

    investigations = test_client.get(f"/api/v1/institution-portal/{institution_id}/investigations")
    assert investigations.status_code == 200
    assert investigations.json()["count"] >= 1

    analytics = test_client.get(f"/api/v1/institution-portal/{institution_id}/analytics")
    assert analytics.status_code == 200
    assert analytics.json()["cases_total"] >= 1
    assert analytics.json()["verified_domains"] >= 1
    assert analytics.json()["active_members"] >= 1


def test_health_reports_phase10_version(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "2.4.0"
    assert health["institution_portal"] is True
