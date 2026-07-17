# ADR-0007: Resilience and scale proof posture

**Status:** Accepted  
**Date:** 2026-07-17  
**Pillar(s):** pillar-infrastructure  
**Transformation phase:** T6 (2.6.0)

## Context

National claims of scale require evidence: load scenarios, multi-AZ deploy patterns, and documented disaster recovery. The monolith remains the runtime (ADR-0001); this phase proves operability, not a rewrite.

## Decision

1. Ship **Locust** and **k6** scenarios for `GET /health`, `POST /api/v1/trust/assess`, and announcement verify paths.
2. Document **Helm multi-AZ** topology and managed Postgres HA expectations (not claim certification).
3. Publish **DR runbook** with RPO/RTO targets and a restore drill checklist.
4. Expose **`GET /api/v1/infra/resilience`** summarizing targets, scripts, and docs (read-only metadata).

## Consequences

- Positive: Operators can run load proofs and follow DR without tribal knowledge.
- Negative: Load results are environment-specific; not a permanent SLA.
- Mitigation: Record drill dates in ops notes; re-run before national go-live.

## Alternatives considered

- **Immediate microservice split for scale:** Rejected (ADR-0001).
- **Only marketing claims without scripts:** Rejected by quality gate.
