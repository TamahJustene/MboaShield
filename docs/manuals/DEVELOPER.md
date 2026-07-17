# Developer manual

**Version:** 1.9.0

## Stack

- FastAPI app factory: `backend/app/main.py`
- Routers: `backend/app/api/v1/*` under `/api/v1`
- SQLAlchemy models + Alembic migrations
- Static frontend under `frontend/static`
- Tests: `backend/tests` (pytest)

## Local setup

```bash
cd mboashield
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
export PYTHONPATH=. JWT_SECRET=dev-secret
uvicorn backend.app.main:app --reload --port 8000
pytest backend/tests -q
```

## API contract rules

1. Do not break `/api/v1/*` without a migration path for clients.
2. Soft auth must keep demo working when `AUTH_ENFORCE=false`.
3. Trust outputs must keep `certainty: "none"` by default.
4. Prefer ASCII in Python string literals (encoding safety).

## Adding a feature (pattern)

1. Config flag in `core/config.py` + `.env.example`
2. Models + Alembic revision (if durable)
3. Store module + router under `api/v1`
4. RBAC permission in `core/rbac.py`
5. Tests + CHANGELOG + PRODUCT_STATUS

## OpenAPI

- Interactive: `/docs`
- Export: `python scripts/export_openapi.py`
- Narrative reference: [API_REFERENCE.md](API_REFERENCE.md)

## Engines

Intelligence engines live in `backend/app/services/engines/`. Heuristic fallbacks are mandatory when advanced runtimes fail (Phase 12).

## Workers (optional)

When `WORKERS_ENABLED=true`, Celery tasks in `backend/app/workers/` handle intel ingest, vault retention, and AI evaluation. Otherwise enqueue helpers run sync.
