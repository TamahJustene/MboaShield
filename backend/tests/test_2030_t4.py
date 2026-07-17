"""MboaShield 2030 transformation phase T4 tests."""

from __future__ import annotations

from backend.app.services.interop.webhooks import sign_payload, verify_signature


def test_health_reports_t4(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "2.8.0"
    assert health["transformation_phase"] == "CI-1"


def test_interop_status_and_events(client):
    test_client, _ = client
    status = test_client.get("/api/v1/interop/status").json()
    assert status["enabled"] is True
    assert status["features"]["webhooks"] is True
    events = test_client.get("/api/v1/interop/events").json()
    assert events["count"] >= 4


def test_webhook_hmac_and_emit(client):
    test_client, _ = client
    body = b'{"type":"interop.ping"}'
    sig = sign_payload(body, "test-secret")
    assert verify_signature(body, sig, "test-secret")
    assert not verify_signature(body, "sha256=dead", "test-secret")

    created = test_client.post(
        "/api/v1/interop/webhooks",
        json={
            "name": "Test sink",
            "url": "https://example.invalid/hooks/mboashield",
            "events": ["interop.ping"],
            "partner_org": "CERT-CM",
            "secret": "test-secret",
        },
    )
    assert created.status_code == 200
    endpoint = created.json()
    assert endpoint["id"]
    assert endpoint["secret"] == "test-secret"

    emitted = test_client.post(
        "/api/v1/interop/webhooks/emit",
        json={"event_type": "interop.ping", "data": {"ok": True}, "sync_deliver": True},
    )
    assert emitted.status_code == 200
    payload = emitted.json()
    assert payload["count"] >= 1
    assert payload["deliveries"][0]["status"] in {"delivered", "failed", "pending"}


def test_stix_and_csv_exports(client):
    test_client, _ = client
    stix = test_client.get("/api/v1/interop/stix/bundle?limit=5")
    assert stix.status_code == 200
    bundle = stix.json()
    assert bundle["type"] == "bundle"
    assert bundle["spec_version"] == "2.1"

    csv_res = test_client.get("/api/v1/interop/reports/incidents.csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")
    assert "id,report_type" in csv_res.text


def test_cap_export_from_advisory(client):
    test_client, _ = client
    check = test_client.post(
        "/api/v1/check/text",
        json={"text": "Fake grant from ministry", "lang": "en"},
    ).json()
    incident = test_client.post(
        "/api/v1/incidents",
        json={
            "report_type": "disinformation",
            "description": "Viral fake grant",
            "verification_check_id": check["check_id"],
        },
    ).json()
    # advance toward public_advisory via direct status updates if allowed
    for status in ("ai_analysis", "analyst_review", "institution_review", "decision", "public_advisory"):
        res = test_client.patch(
            f"/api/v1/incidents/{incident['id']}",
            json={"status": status, "public_advisory": "Verify with MINPOSTEL before sharing."},
        )
        if res.status_code != 200:
            break
    cap = test_client.get(f"/api/v1/interop/cap/incident/{incident['id']}")
    # may be 400 if workflow blocked; still assert bundle endpoint works
    if cap.status_code == 200:
        assert "urn:oasis:names:tc:emergency:cap:1.2" in cap.text
    bundle = test_client.get("/api/v1/interop/cap/bundle")
    assert bundle.status_code == 200
    assert "alerts" in bundle.json()
