# Phase 8 - Threat Intelligence Platform (compliant sources)

**Version:** 1.2.0  
**Status:** COMPLETE  
**Date:** 16 July 2026  

## Delivered

- Source registry with compliance metadata (`tos_reference`, license, source class)
- Compliant connectors only: `rss`, `official_api`, `open_data`, `partner_webhook`
- Explicit rejection of scrape / ToS-bypass source classes
- Egress host allowlist (`INTEL_EGRESS_ALLOWLIST`)
- Ingest (pull) + partner webhook push
- Correlation to incidents + campaign clustering
- National intel report (JSON + markdown)
- Alembic `0007_phase8`
- Ops UI: `/static/intel.html`

## Key APIs

| Path | Purpose |
|---|---|
| `GET /api/v1/intel/source-classes` | Allowed vs forbidden classes |
| `/api/v1/intel/sources*` | Register, list, enable/disable, ingest |
| `POST /api/v1/intel/webhook/{id}` | Partner push ingest |
| `/api/v1/intel/items` | List/search items |
| `POST /api/v1/intel/correlate` | Correlate + cluster campaigns |
| `/api/v1/intel/campaigns` | Campaign list |
| `GET /api/v1/intel/reports/national` | National report |

## Compliance

Collection is limited to official APIs, RSS/Atom, open data, and authorized partner webhooks. Scraping connectors are forbidden in code.

## Tests

Phase 8 tests green; full suite green at close (63 passed).

## Rollback

Set `INTEL_ENABLED=false`.
