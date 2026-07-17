# Phase T7 - Country packs & sector modules (MboaShield 2030)

**Version:** 2.7.0  
**Status:** COMPLETE  

## Delivered

- ADR-0008: Country packs and sector modules
- Expanded `deploy/country-packs/cm` + `template` packs (legal, IdP, sectors)
- `GET /api/v1/country-pack`, `GET /api/v1/sectors`
- Sector dashboard: `/static/sectors.html`
- Governance framework map: ISO/NIST IDs on controls (`/api/v1/governance/framework-map`)
- Config: `SECTORS_ENABLED`
- Tests: `test_2030_t7.py`

## Program status

Transformation phases **T0-T7** complete for the 2030 plan baseline (2.0.0-2.7.0).

## Rollback

Revert to v2.6.0; pack/sector APIs are additive.
