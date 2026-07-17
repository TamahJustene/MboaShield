# ADR-0001: Monolith-first national platforms

**Status:** Accepted  
**Date:** 2026-07-17  
**Pillar(s):** All

## Context

MboaShield 2030 targets national-scale infrastructure with ten permanent platforms. The codebase is a modular FastAPI monolith (v1.9) with optional Celery workers and Helm chart. Premature microservice decomposition would slow delivery and complicate operations for a solo/small team serving government pilots.

## Decision

1. Implement national **platforms** as **logical boundaries** (packages, OpenAPI tags, docs, RBAC) inside one deployable Trust API until load and organizational boundaries justify extraction.
2. Preserve `/api/v1` contracts; add new namespaces additively (`/trust`, `/trust-network`, etc.).
3. Use feature flags and `DEPLOYMENT_PROFILE` / `COUNTRY_PACK` for multi-country and gov vs demo behavior.
4. Extract services only when a pillar has independent scaling needs **proven** by metrics (Phase T6).

## Consequences

- Positive: Faster iteration, simpler deploy for Cameroon pilot, aligns with existing Phase 13 Helm/worker split path.
- Negative: Must enforce modular discipline in code reviews to avoid spaghetti monolith.
- Mitigation: Pillar registry, ADRs, quality gates per transformation phase.

## Alternatives considered

- **Immediate microservices:** Rejected — operational cost and network complexity without proven scale.
- **Rewrite in another stack:** Rejected — destroys working `/api/v1` and competition/demo stability.
