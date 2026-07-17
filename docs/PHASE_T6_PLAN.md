# Phase T6 - Resilience & scale proof (MboaShield 2030)

**Version:** 2.6.0  
**Status:** COMPLETE  

## Delivered

- ADR-0007: Resilience and scale proof
- Locust: `scripts/load/locustfile.py`
- k6: `scripts/load/trust_assess.js`
- Helm multi-AZ / Postgres HA: `docs/HA_AND_SCALE.md`
- DR runbook + drill: `docs/DR_RUNBOOK.md` (linked from OPERATIONS)
- `GET /api/v1/infra/resilience`
- Tests: `test_2030_t6.py`

## Targets (indicative)

| Metric | Target (pilot) |
|---|---|
| RPO | <= 15 minutes (managed Postgres PITR) |
| RTO | <= 4 hours (restore + DNS cutover) |
| Trust assess p95 | Document after Locust/k6 run on target hardware |

## Not in T6 (T7)

- Country packs / sector modules expansion

## Rollback

Revert to v2.5.0; resilience endpoint and docs are additive.
