"""Phase 8 compliant threat intelligence tests."""

from __future__ import annotations

from backend.app.services.intel.connectors import parse_rss_or_atom


SAMPLE_RSS = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Gov Feed</title>
    <item>
      <title>Alert about @FakeBankCM scam https://example.cm/scam</title>
      <link>https://example.cm/alerts/1</link>
      <guid>gov-1</guid>
      <description>Public advisory mentioning @FakeBankCM</description>
      <pubDate>Thu, 16 Jul 2026 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Second advisory @FakeBankCM</title>
      <link>https://example.cm/alerts/2</link>
      <guid>gov-2</guid>
      <description>Follow-up https://example.cm/scam</description>
    </item>
  </channel>
</rss>
"""


def test_parse_rss_extracts_handles_and_urls():
    items = parse_rss_or_atom(SAMPLE_RSS)
    assert len(items) == 2
    assert items[0].external_id == "gov-1"
    assert "@FakeBankCM" in items[0].handles
    assert "https://example.cm/scam" in items[0].urls or "https://example.cm/alerts/1" in items[0].urls


def test_rejects_scrape_source_class(client):
    test_client, _ = client
    response = test_client.post(
        "/api/v1/intel/sources",
        json={
            "name": "Bad scraper",
            "source_class": "html_scrape",
            "endpoint_url": "https://example.com",
            "tos_reference": "none",
        },
    )
    assert response.status_code == 400
    msg = response.json()["error"]["message"]
    assert "Allowed" in msg or "Unsupported" in msg


def test_partner_webhook_ingest_correlate_and_report(client):
    test_client, _ = client
    source = test_client.post(
        "/api/v1/intel/sources",
        json={
            "name": "CERT push",
            "source_class": "partner_webhook",
            "endpoint_url": "webhook://cert",
            "tos_reference": "Partner MoU clause 4",
            "license": "partner-restricted",
        },
    )
    assert source.status_code == 200
    source_id = source.json()["id"]
    assert source.json()["compliance"]["allowed_source_class"] is True

    incident = test_client.post(
        "/api/v1/incidents",
        json={
            "report_type": "disinformation",
            "description": "Citizens report @FakeBankCM and https://example.cm/scam spreading on WhatsApp",
            "region": "Littoral",
        },
    )
    assert incident.status_code == 200

    pushed = test_client.post(
        f"/api/v1/intel/webhook/{source_id}",
        json={
            "items": [
                {
                    "id": "wh-1",
                    "title": "Partner sighting of @FakeBankCM",
                    "summary": "See https://example.cm/scam",
                    "url": "https://partner.example.cm/i/1",
                },
                {
                    "id": "wh-2",
                    "title": "Second sighting @FakeBankCM",
                    "summary": "Same https://example.cm/scam cluster",
                    "url": "https://partner.example.cm/i/2",
                },
            ]
        },
    )
    assert pushed.status_code == 200
    assert pushed.json()["created"] == 2

    items = test_client.get("/api/v1/intel/items")
    assert items.status_code == 200
    assert items.json()["count"] >= 2

    correlated = test_client.post("/api/v1/intel/correlate")
    assert correlated.status_code == 200
    assert correlated.json()["correlations_created"] >= 1
    assert correlated.json()["campaigns_created"] >= 1

    report = test_client.get("/api/v1/intel/reports/national")
    assert report.status_code == 200
    body = report.json()
    assert "compliance_note" in body
    assert "markdown" in body
    assert body["summary"]["items"] >= 2

    md = test_client.get("/api/v1/intel/reports/national?format=markdown")
    assert md.status_code == 200
    assert "National Threat Intelligence Report" in md.text


def test_rss_ingest_with_mocked_fetch(client, monkeypatch):
    test_client, _ = client
    source = test_client.post(
        "/api/v1/intel/sources",
        json={
            "name": "Mock RSS",
            "source_class": "rss",
            "endpoint_url": "https://feeds.example.cm/rss.xml",
            "tos_reference": "https://feeds.example.cm/terms",
            "license": "rss-public",
        },
    )
    assert source.status_code == 200
    source_id = source.json()["id"]

    class FakeResponse:
        text = SAMPLE_RSS

        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("backend.app.services.intel.connectors.httpx.Client", FakeClient)
    ingested = test_client.post(f"/api/v1/intel/sources/{source_id}/ingest")
    assert ingested.status_code == 200
    assert ingested.json()["created"] == 2


def test_health_reports_phase8_version(client):
    test_client, _ = client
    health = test_client.get("/health").json()
    assert health["version"] == "2.8.0"
    assert health["intel"] is True
