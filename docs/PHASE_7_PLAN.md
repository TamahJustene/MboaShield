# Phase 7 — National Trust Operations Center

**Version:** 1.1.0  
**Status:** COMPLETE  
**Date:** 16 July 2026  

## Delivered

- NTOC dashboard UI (`/static/ntoc.html`)
- Threat level service + regional offline map
- Cases API: create, search, assign, notes, workspace, evidence read-path
- Notifications (in-app + optional webhook)
- Institution health scores + snapshots
- Investigation workspace UI (`/static/investigation.html`)
- Alembic `0006_phase7`
- Incident transitions emit analyst notifications

## Key APIs

| Path | Purpose |
|---|---|
| `GET /api/v1/ntoc/dashboard` | Live ops dashboard |
| `GET /api/v1/ntoc/threat-level` | National threat level |
| `GET /api/v1/ntoc/regions` | Regional intensity |
| `GET /api/v1/ntoc/institution-health` | Institution health |
| `/api/v1/cases*` | Casework |
| `/api/v1/notifications*` | Notifications |

## Tests

Phase 7 tests green; full suite run at close.

## Rollback

Set `NTOC_ENABLED=false`.
