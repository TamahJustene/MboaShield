# Phase 11 - Verified Government Communications

**Version:** 1.5.0  
**Status:** COMPLETE  
**Date:** 16 July 2026  

## Delivered

- Signed announcement lifecycle (draft, publish, version, revoke)
- HMAC signatures with `signing_kid` (env: `ANNOUNCEMENT_SIGNING_KEY` / vault fallback)
- Permanent public verify URL: `GET /verify/a/{announcement_id}`
- QR payload + JSON/markdown authenticity certificate
- Version history (published versions only in public list)
- Publisher UI + public verify UI
- Alembic `0010_phase11`
- Feature flag: `VERIFIED_COMMS_ENABLED`

## Key APIs

| Path | Purpose |
|---|---|
| `/api/v1/announcements*` | Draft, publish, revoke, verify, QR, certificate |
| `GET /verify/a/{id}` | Public verification (no auth) |
| `GET /verify/a/{id}/certificate` | Public certificate export |

## UI

- `/static/announcements.html` - publish workflow
- `/static/verify-announcement.html` - citizen verify

## Rollback

Set `VERIFIED_COMMS_ENABLED=false`.
