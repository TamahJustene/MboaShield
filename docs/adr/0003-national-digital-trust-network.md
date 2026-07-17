# ADR-0003: National Digital Trust Network

**Status:** Accepted  
**Date:** 2026-07-17  
**Pillar(s):** pillar-partner, pillar-identity  
**Transformation phase:** T2 (2.2.0)

## Context

Institutions on MboaShield (CERT, banks, telcos, ministries) need controlled collaboration: who trusts whom, which channels exist for exchange, and typed shared alerts with audit. Today each institution portal is siloed.

## Decision

1. Persist **`trust_relationship`** between two institution IDs with status (`pending` | `active` | `suspended` | `revoked`) and optional policy notes.
2. Persist **`exchange_channel`** on a relationship (or bilateral pair) for typed exchange (`alert_share`, `ioc_exchange`, `advisory`).
3. Persist **`shared_alert`** with types: `impersonation`, `deepfake`, `fraud`, `ioc`, `advisory`; source institution, optional target institutions (JSON list), severity, and payload.
4. Expose additive APIs under **`/api/v1/trust-network/*`** without changing existing institution-portal routes.
5. Soft-auth demo profile remains; government deployments enforce RBAC via existing `institutions:manage` / partner scopes when `AUTH_ENFORCE=true`.

## Consequences

- Positive: Pilot multi-institution alert sharing with audit trail.
- Negative: No real-time push yet (T4 webhooks).
- Mitigation: List/inbox APIs for polling; link alerts to verification_check / trust_assessment IDs when available.

## Alternatives considered

- **Reuse incident reports only:** Rejected - incidents are workflow cases, not partner exchange objects.
- **Immediate STIX TAXII:** Deferred to T4.
