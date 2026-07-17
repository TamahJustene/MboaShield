# ADR-0004: Shared portal shell

**Status:** Accepted  
**Date:** 2026-07-17  
**Pillar(s):** All (UX platform)  
**Transformation phase:** T3 (2.3.0)

## Context

MboaShield has many static HTML portals with duplicated headers, auth token handling, and navigation. National infrastructure needs a consistent shell (auth awareness, tenant, FR/EN) without rewriting every page in one release.

## Decision

1. Ship **`portal-shell.js`** as the shared shell: injects brand header, portal nav, auth status, tenant line, and language toggle.
2. Migrate **Analyst**, **NTOC**, and **Institution portal** first; other pages remain standalone until later increments.
3. Add **`/static/developer.html`** as the developer portal (API keys entry, OpenAPI, webhook roadmap).
4. Shell reads `/health` and `/api/v1/program` for version/tenant/phase; language preference stored in `localStorage` (`mboashield_lang`).
5. Do not break page-specific scripts; shell exposes `window.MboaShieldPortal` helpers (`authHeaders`, `getLang`, `t`).

## Consequences

- Positive: Consistent ops UX; faster future portal migrations.
- Negative: Two header patterns until all pages migrate.
- Mitigation: Hub links developer portal; document migration checklist in PHASE_T3_PLAN.

## Alternatives considered

- **SPA rewrite (React/Vue):** Rejected for T3 - too large vs additive static evolution.
- **Server-side templates only:** Deferred - current deploy serves static files from FastAPI.
