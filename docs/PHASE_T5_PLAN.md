# Phase T5 - Zero-trust & identity scale (MboaShield 2030)

**Version:** 2.5.0  
**Status:** COMPLETE  

## Delivered

- ADR-0006: Zero-trust national identity default
- `deploy/profiles/national.env` - AUTH_ENFORCE=true national profile
- Zero-trust checklist on `GET /api/v1/auth/security-status`
- SCIM 2.0 read-only: `/scim/v2/Users`, `/scim/v2/ServiceProviderConfig`
- Postgres RLS template: `deploy/sql/rls_tenant.sql`
- KMS / secrets guide: `docs/manuals/KMS_AND_SECRETS.md`
- Tests: `test_2030_t5.py`

## Not in T5 (T6+)

- Full SCIM write provisioning
- Load / HA proof

## Rollback

Revert to v2.4.0; SCIM routes are additive.
