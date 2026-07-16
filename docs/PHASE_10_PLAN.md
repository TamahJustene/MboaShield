# Phase 10 - Institution Administration Platform

**Version:** 1.4.0  
**Status:** COMPLETE  
**Date:** 16 July 2026  

## Delivered

- Institution portal under `/api/v1/institution-portal/*`
- Domain registration + verification (`dns_txt`, `token_confirm`, `http_file`)
- Memberships (invite by email or attach user_id; member/admin roles)
- Branding JSON + contact email on institutions
- Official accounts registry
- Institution-scoped API keys (`msi_` prefix) authenticated alongside partner `msb_` keys
- Institution investigations list + analytics summary
- Membership enforcement when `AUTH_ENFORCE=true`
- UI: `/static/institution-portal.html` (+ registry link)
- Alembic `0009_phase10`
- Feature flag: `INSTITUTION_PORTAL_ENABLED`

## Key APIs

| Path | Purpose |
|---|---|
| `GET .../health` | Portal enabled + institution count |
| `GET .../{id}/overview` | Combined portal snapshot |
| `.../domains` + `.../verify` | Domain workflow |
| `.../memberships` | Invite / update members |
| `GET/PUT .../branding` | Branding config |
| `.../official-accounts` | Official handles |
| `.../api-keys` | Scoped `msi_` keys |
| `.../investigations` | Cases for institution |
| `.../analytics` | Counts |

## Rollback

Set `INSTITUTION_PORTAL_ENABLED=false`.
