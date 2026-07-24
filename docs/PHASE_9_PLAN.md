# Phase 9 - Digital Evidence Vault

**Version:** 1.3.0  
**Status:** COMPLETE  
**Date:** 16 July 2026  

## Delivered

- Evidence registration (JSON base64 + multipart upload)
- Local filesystem storage adapter (demo) + optional S3 adapter (`VAULT_STORAGE=s3`, requires boto3)
- SHA-256 content hashing + integrity check on read
- Append-only custody chain with hash linking
- Custody transfer
- Signed JSON export packages (HMAC) + verify endpoint
- Retention dry-run / purge (objects deleted; custody retained)
- Case workspace shows vault items + upload form
- Alembic `0008_phase9`
- Feature flag: `VAULT_ENABLED`

## Key APIs

| Path | Purpose |
|---|---|
| `GET /api/v1/evidence/health` | Vault config summary |
| `POST /api/v1/evidence` | Register (JSON or multipart) |
| `GET /api/v1/evidence` | List / search |
| `GET /api/v1/evidence/{id}` | Metadata |
| `GET /api/v1/evidence/{id}/download` | Bytes (hash verified) |
| `GET /api/v1/evidence/{id}/custody` | Chain + validity |
| `POST /api/v1/evidence/{id}/transfer` | Custody transfer |
| `POST /api/v1/evidence/{id}/export` | Signed package |
| `GET /api/v1/evidence/exports/{id}/verify` | Verify signature/hash |
| `POST /api/v1/evidence/retention/run` | Retention dry-run/purge |

## Permissions

- `evidence:read` - analyst, institution_admin, admin
- `evidence:write` - analyst, admin
- `evidence:manage` - admin (retention)

## Tests

Phase 9 tests green; full suite run at close.

## Rollback

Set `VAULT_ENABLED=false`.
