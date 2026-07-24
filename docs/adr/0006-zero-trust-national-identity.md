# ADR-0006: Zero-trust national identity default

**Status:** Accepted  
**Date:** 2026-07-17  
**Pillar(s):** pillar-identity  
**Transformation phase:** T5 (2.5.0)

## Context

Demo deployments use soft auth (`AUTH_ENFORCE=false`) for demo continuity. National government deployments require enforced authentication, IdP federation readiness, and a path to SCIM provisioning and Postgres row-level security.

## Decision

1. Keep **demo default** soft-auth; publish **`deploy/profiles/national.env`** with `AUTH_ENFORCE=true` and `DEPLOYMENT_PROFILE=national` as the national default.
2. Extend `/api/v1/auth/security-status` with a **zero-trust checklist** (`zero_trust`).
3. Ship **SCIM 2.0 read-only** Users listing at `/scim/v2/Users` (Bearer / soft-auth for demo); write/provisioning deferred.
4. Provide **Postgres RLS** SQL template (`deploy/sql/rls_tenant.sql`) applied manually for gov Postgres; SQLite demos skip RLS.
5. Document **KMS / secrets** guidance: no long-lived secrets in env for production; inject via KMS/secret manager.

## Consequences

- Positive: Clear national posture without breaking public demo.
- Negative: SCIM is read-only; RLS not auto-applied on SQLite.
- Mitigation: Tests assert checklist + SCIM list; ops manuals point to national profile.

## Alternatives considered

- **Flip AUTH_ENFORCE default to true:** Rejected - breaks Render public demo and demo soft-auth.
- **Full SCIM write:** Deferred until IdP pilot requires it.
