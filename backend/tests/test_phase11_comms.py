"""Phase 11 verified government communications tests."""

from __future__ import annotations


def test_announcement_publish_verify_public_and_revoke(client):
    test_client, _ = client
    inst = test_client.post(
        "/api/v1/institutions",
        json={
            "id": "comms-demo",
            "name": "Comms Demo Ministry",
            "short_name": "CommsDemo",
            "url": "https://comms-demo.cm",
            "handles": ["@CommsDemo"],
            "verified": True,
        },
    )
    assert inst.status_code == 200

    draft = test_client.post(
        "/api/v1/announcements",
        json={
            "institution_id": "comms-demo",
            "title": "Official curfew update",
            "body": "Citizens are informed that the evening curfew remains 22:00 until further notice.",
            "locale": "en",
        },
    )
    assert draft.status_code == 200, draft.text
    announcement_id = draft.json()["announcement_id"]

    published = test_client.post(
        f"/api/v1/announcements/{announcement_id}/publish",
        json={},
    )
    assert published.status_code == 200, published.text
    assert published.json()["status"] == "published"
    assert published.json()["version"]["signature"]
    version = published.json()["version"]["version_number"]

    public = test_client.get(f"/verify/a/{announcement_id}")
    assert public.status_code == 200
    body = public.json()
    assert body["valid"] is True
    assert body["signature_valid"] is True
    assert "curfew" in body["body"].lower()

    qr = test_client.get(f"/api/v1/announcements/{announcement_id}/qr")
    assert qr.status_code == 200
    assert qr.json()["verify_url"].startswith("http")

    cert = test_client.get(f"/verify/a/{announcement_id}/certificate")
    assert cert.status_code == 200
    assert cert.json()["verification"]["valid"] is True

    republish = test_client.post(
        f"/api/v1/announcements/{announcement_id}/publish",
        json={"body": "Updated: curfew now 21:00 nationwide until reviewed by authorities."},
    )
    assert republish.status_code == 200
    assert republish.json()["current_version"] == version + 1

    versions = test_client.get(f"/api/v1/announcements/{announcement_id}")
    assert versions.status_code == 200
    assert len(versions.json()["versions"]) >= 2

    revoked = test_client.post(f"/api/v1/announcements/{announcement_id}/revoke")
    assert revoked.status_code == 200
    after = test_client.get(f"/verify/a/{announcement_id}")
    assert after.json()["valid"] is False
    assert after.json()["status"] == "revoked"


def test_health_reports_phase11_version(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "1.5.0"
    assert health["verified_comms"] is True
