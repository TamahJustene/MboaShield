# Maintenance manual

**Version:** 1.9.0

## Routine

| Cadence | Task |
|---|---|
| Daily | Check `/health`, disk for vault path, error rates in metrics |
| Weekly | Review open risks; dry-run vault retention |
| Monthly | Rotate signing keys (kid versioning); review partner keys |
| Per release | `pytest`; Alembic upgrade; CHANGELOG; smoke guided demo |

## Database

- Backup Postgres with managed PITR where available.
- After restore: `alembic upgrade head` if schema lag.
- SQLite demo DB path: `storage/mboashield.db` (do not use for gov).

## Evidence vault

- Retention: `VAULT_RETENTION_DAYS` + `POST /api/v1/evidence/retention/run` or infra job.
- Object storage: local FS or S3 (`VAULT_STORAGE`).
- Custody events remain after purge of blobs.

## AI assets

- Weights under `data/` - verify checksums via `/api/v1/ai-platform/models/{id}/verify-checksum`
- Golden sets: `data/ai_golden_en.json`, `data/ai_golden_fr.json`
- Re-run evaluation after engine changes

## Dependency hygiene

```bash
pip install -r backend/requirements.txt
# Prefer pip-audit / OSV in CI before government go-live
```

## Documentation refresh

```bash
python scripts/export_openapi.py
```

Update manuals when adding API surfaces or changing auth behaviour.
