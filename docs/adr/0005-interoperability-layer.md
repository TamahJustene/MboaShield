# ADR-0005: Interoperability layer (webhooks, STIX, CAP)

**Status:** Accepted  
**Date:** 2026-07-17  
**Pillar(s):** pillar-partner, pillar-intel, pillar-comms  
**Transformation phase:** T4 (2.4.0)

## Context

National systems and partners need to consume MboaShield events and intelligence without scraping the UI. Phase 8 already supports inbound partner webhooks for intel. T4 adds outbound interoperability.

## Decision

1. Expose **`/api/v1/interop/*`** for outbound webhook subscriptions, event catalog, STIX export, CAP export, and CSV national reports.
2. Sign outbound webhook payloads with **HMAC-SHA256** (`X-MboaShield-Signature: sha256=<hex>`) using `WEBHOOK_SIGNING_SECRET` (falls back to `JWT_SECRET` in demo).
3. Persist delivery attempts with status and retry count (sync retry up to N times for the pilot; async workers remain optional).
4. STIX 2.1 **read-only** bundle from intel items (pilot, not a full TAXII server).
5. CAP 1.2 XML from incidents in `public_advisory` status.
6. Keep existing `/api/v1` contracts unchanged.

## Consequences

- Positive: Partners can integrate with signed events and standard formats.
- Negative: Not a production TAXII server yet; CAP is a subset.
- Mitigation: Document limits in developer portal; expand in later releases.

## Alternatives considered

- **Only env-based single webhook URL:** Insufficient for multi-partner national deploy.
- **Full TAXII 2.1 server:** Deferred past pilot.
