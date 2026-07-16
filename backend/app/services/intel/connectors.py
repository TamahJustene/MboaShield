"""Compliant threat-intelligence connectors.

Allowed source classes only:
- rss (RSS/Atom)
- official_api (vendor/official HTTP JSON APIs with credentials)
- open_data (government open-data HTTP endpoints)
- partner_webhook (push ingest; no egress scrape)

Forbidden: undocumented scraping, ToS bypass, credential stuffing.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx
from defusedxml import ElementTree as DET

from ...core.config import get_settings

ALLOWED_SOURCE_CLASSES = {"rss", "official_api", "open_data", "partner_webhook"}
HANDLE_RE = re.compile(r"(?<![A-Za-z0-9_])@([A-Za-z0-9_]{2,32})")
URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)


@dataclass
class NormalizedIntelItem:
    external_id: str
    title: str
    summary: str | None = None
    url: str | None = None
    published_at: str | None = None
    handles: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def content_hash(self) -> str:
        blob = f"{self.external_id}|{self.title}|{self.summary or ''}|{self.url or ''}"
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class IntelConnector(Protocol):
    source_class: str

    def fetch(self, *, endpoint_url: str, config: dict[str, Any], credentials: dict[str, Any] | None) -> list[NormalizedIntelItem]:
        ...


def assert_allowed_source_class(source_class: str) -> str:
    value = (source_class or "").strip().lower()
    if value not in ALLOWED_SOURCE_CLASSES:
        raise ValueError(
            f"Unsupported source_class '{source_class}'. Allowed: {', '.join(sorted(ALLOWED_SOURCE_CLASSES))}. "
            "Scraping connectors are forbidden."
        )
    if value in {"scrape", "html_scrape", "browser_scrape"}:
        raise ValueError("Scraping is forbidden by MboaShield compliance policy")
    return value


def extract_signals(text: str) -> tuple[list[str], list[str]]:
    handles = sorted({f"@{m.group(1)}" for m in HANDLE_RE.finditer(text or "")})
    urls = sorted({m.group(0).rstrip(").,;") for m in URL_RE.finditer(text or "")})
    return handles, urls


def assert_egress_allowed(endpoint_url: str) -> str:
    parsed = urlparse(endpoint_url)
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("endpoint_url must include a host")
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("endpoint_url must use http or https")
    allowlist = get_settings().intel_allowlist_hosts()
    if allowlist is not None and host not in allowlist:
        raise ValueError(f"Host '{host}' is not in INTEL_EGRESS_ALLOWLIST")
    return host


class RssConnector:
    source_class = "rss"

    def fetch(self, *, endpoint_url: str, config: dict[str, Any], credentials: dict[str, Any] | None) -> list[NormalizedIntelItem]:
        assert_egress_allowed(endpoint_url)
        headers = {"User-Agent": "MboaShieldIntel/1.2 (+compliant-rss; government-trust-platform)"}
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = client.get(endpoint_url, headers=headers)
            response.raise_for_status()
            xml_text = response.text
        return parse_rss_or_atom(xml_text, limit=int(config.get("limit") or get_settings().intel_ingest_limit))


class OfficialApiConnector:
    source_class = "official_api"

    def fetch(self, *, endpoint_url: str, config: dict[str, Any], credentials: dict[str, Any] | None) -> list[NormalizedIntelItem]:
        assert_egress_allowed(endpoint_url)
        headers = {"Accept": "application/json", "User-Agent": "MboaShieldIntel/1.2 (+official-api)"}
        creds = credentials or {}
        if creds.get("bearer_token"):
            headers["Authorization"] = f"Bearer {creds['bearer_token']}"
        if creds.get("api_key_header") and creds.get("api_key"):
            headers[str(creds["api_key_header"])] = str(creds["api_key"])
        params = config.get("params") if isinstance(config.get("params"), dict) else {}
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = client.get(endpoint_url, headers=headers, params=params)
            response.raise_for_status()
            payload = response.json()
        return normalize_api_payload(payload, limit=int(config.get("limit") or get_settings().intel_ingest_limit))


class OpenDataConnector(OfficialApiConnector):
    source_class = "open_data"


class PartnerWebhookConnector:
    """Push-only; fetch is not used for egress."""

    source_class = "partner_webhook"

    def fetch(self, *, endpoint_url: str, config: dict[str, Any], credentials: dict[str, Any] | None) -> list[NormalizedIntelItem]:
        return []


CONNECTORS: dict[str, IntelConnector] = {
    "rss": RssConnector(),
    "official_api": OfficialApiConnector(),
    "open_data": OpenDataConnector(),
    "partner_webhook": PartnerWebhookConnector(),
}


def get_connector(source_class: str) -> IntelConnector:
    key = assert_allowed_source_class(source_class)
    return CONNECTORS[key]


def parse_rss_or_atom(xml_text: str, *, limit: int = 50) -> list[NormalizedIntelItem]:
    root = DET.fromstring(xml_text.encode("utf-8") if isinstance(xml_text, str) else xml_text)
    tag = root.tag.lower() if isinstance(root.tag, str) else ""
    items: list[NormalizedIntelItem] = []

    # RSS 2.0
    for node in root.findall(".//item"):
        title = (node.findtext("title") or "").strip() or "Untitled"
        link = (node.findtext("link") or "").strip() or None
        guid = (node.findtext("guid") or link or title).strip()
        summary = (node.findtext("description") or "").strip() or None
        published = (node.findtext("pubDate") or "").strip() or None
        blob = f"{title} {summary or ''} {link or ''}"
        handles, urls = extract_signals(blob)
        if link and link not in urls:
            urls.append(link)
        items.append(
            NormalizedIntelItem(
                external_id=guid,
                title=title[:512],
                summary=summary,
                url=link,
                published_at=published,
                handles=handles,
                urls=urls,
                raw={"format": "rss"},
            )
        )
        if len(items) >= limit:
            return items

    # Atom
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for node in root.findall(".//{http://www.w3.org/2005/Atom}entry") or root.findall(".//atom:entry", ns):
        title = (node.findtext("{http://www.w3.org/2005/Atom}title") or node.findtext("title") or "").strip() or "Untitled"
        link = None
        for link_el in node.findall("{http://www.w3.org/2005/Atom}link"):
            if link_el.attrib.get("rel", "alternate") in {"alternate", ""}:
                link = link_el.attrib.get("href")
                break
        if not link:
            link_el = node.find("link")
            if link_el is not None:
                link = link_el.attrib.get("href")
        entry_id = (
            node.findtext("{http://www.w3.org/2005/Atom}id")
            or node.findtext("id")
            or link
            or title
        ).strip()
        summary = (
            node.findtext("{http://www.w3.org/2005/Atom}summary")
            or node.findtext("summary")
            or ""
        ).strip() or None
        published = (
            node.findtext("{http://www.w3.org/2005/Atom}updated")
            or node.findtext("{http://www.w3.org/2005/Atom}published")
            or ""
        ).strip() or None
        blob = f"{title} {summary or ''} {link or ''}"
        handles, urls = extract_signals(blob)
        if link and link not in urls:
            urls.append(link)
        items.append(
            NormalizedIntelItem(
                external_id=entry_id,
                title=title[:512],
                summary=summary,
                url=link,
                published_at=published,
                handles=handles,
                urls=urls,
                raw={"format": "atom", "root": tag},
            )
        )
        if len(items) >= limit:
            break
    return items


def normalize_api_payload(payload: Any, *, limit: int = 50) -> list[NormalizedIntelItem]:
    rows: list[Any]
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        for key in ("items", "results", "data", "entries", "articles"):
            if isinstance(payload.get(key), list):
                rows = payload[key]
                break
        else:
            rows = [payload]
    else:
        raise ValueError("Official API payload must be JSON object or array")

    items: list[NormalizedIntelItem] = []
    for row in rows[:limit]:
        if not isinstance(row, dict):
            continue
        title = str(row.get("title") or row.get("name") or row.get("headline") or "Untitled")[:512]
        external_id = str(row.get("id") or row.get("guid") or row.get("url") or title)
        summary = row.get("summary") or row.get("description") or row.get("content")
        summary = str(summary) if summary is not None else None
        url = row.get("url") or row.get("link")
        url = str(url) if url else None
        published = row.get("published_at") or row.get("published") or row.get("date")
        published = str(published) if published else None
        blob = f"{title} {summary or ''} {url or ''} {json.dumps(row, ensure_ascii=True)[:1000]}"
        handles, urls = extract_signals(blob)
        if url and url not in urls:
            urls.append(url)
        items.append(
            NormalizedIntelItem(
                external_id=external_id,
                title=title,
                summary=summary,
                url=url,
                published_at=published,
                handles=handles,
                urls=urls,
                raw={"format": "json"},
            )
        )
    return items


def normalize_webhook_payload(payload: dict[str, Any]) -> list[NormalizedIntelItem]:
    if "items" in payload and isinstance(payload["items"], list):
        return normalize_api_payload(payload["items"])
    return normalize_api_payload([payload])
