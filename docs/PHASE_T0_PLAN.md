# Phase T0 - Architecture alignment (MboaShield 2030)

**Version:** 2.0.0  
**Status:** COMPLETE  

## Delivered

- National platform OpenAPI tags (`pillar-*`) on all routers
- `GET /api/v1/program` — program metadata + pillar catalog
- `/health` extended: `program`, `transformation_phase`, `country_pack`
- `COUNTRY_PACK` configuration (default `cm`)
- Country pack docs: `deploy/country-packs/cm/`, `template/`
- ADR-0001 monolith-first national platforms
- Vision + transformation plan + pillar registry (prior commit)

## Not in T0 (T1+)

- Unified TrustAssessment API
- Trust network exchange
- Portal shell refactor

## Rollback

Revert to v1.9.0 tag; OpenAPI tag names are documentation-only and do not break `/api/v1` paths.
