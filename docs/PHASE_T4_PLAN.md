# Phase T4 - Interoperability layer (MboaShield 2030)

**Version:** 2.4.0  
**Status:** COMPLETE  

## Delivered

- ADR-0005: Interoperability layer
- Outbound webhooks: catalog, subscriptions, HMAC, delivery + retry
- STIX 2.1 read-only intel bundle
- CAP 1.2 export from `public_advisory` incidents
- CSV national incident report export
- Alembic `0017_t4_interop`
- Developer portal updated
- Tests: `test_2030_t4.py`

## Not in T4 (T5+)

- Full TAXII server
- SCIM / zero-trust defaults

## Rollback

Revert to v2.3.0; drop migration `0017_t4_interop`.
