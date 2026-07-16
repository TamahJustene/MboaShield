# MboaShield Architecture

## Current state (v0.5.0 — Phase 1 foundation)

```text
Browser UI (frontend/)
        |
        v
FastAPI create_app() (backend/app/main.py)
        |
        +-- api/v1/auth.py          JWT register/login/refresh
        +-- api/v1/platform.py      checks, incidents, institutions, ambassadors
        |
        +-- core/config.py          settings (env-driven)
        +-- core/security.py        JWT + password hashing
        +-- core/rbac.py            role permissions
        +-- core/middleware.py      request ID, headers, rate limit
        +-- core/errors.py          standard error envelope
        |
        +-- db/models.py            SQLAlchemy models
        +-- db/session.py           SQLite / PostgreSQL engine
        +-- repositories.py         persistence service layer
        |
        +-- services/*              detectors + AI trust engine (unchanged contracts)

Static data (data/*.json)
Alembic migrations (backend/alembic/)
Docker Compose (api + postgres)
```

## Product domains

1. `verification` — text rumours, links, source verification, scam signals
2. `impersonation` — fake account detection, registry matching
3. `synthetic_media` — audio, image (video later)
4. `citizenship` — Ambassadors, certificates
5. `identity` — users, JWT auth, RBAC (Phase 1)
6. `governance` — audit logs, incident review trail (Phase 1 skeleton)

## Database

- Default: SQLite (`storage/mboashield.db` or `MBOASHIELD_DB_PATH`)
- Production: PostgreSQL via `DATABASE_URL=postgresql+psycopg://...`
- Schema created by SQLAlchemy `create_all` plus Alembic for formal migrations
- Soft column upgrades for legacy SQLite user tables

## Security model

| Control | Status |
|---|---|
| JWT access + refresh | Implemented |
| Password hashing (bcrypt) | Implemented |
| Account lockout | Implemented (5 failures / 15 min) |
| RBAC | Ready (`AUTH_ENFORCE=true` to enforce) |
| Audit logs | Implemented |
| Rate limiting | Implemented |
| Security headers | Implemented |
| CORS | Configurable |
| OAuth2 / OIDC / MFA | Scaffolded for Phase 2+ |

Legacy demo header `X-MboaShield-User-Id` remains supported when auth is soft.

## AI layer

Detectors remain modular under `services/`. The trust engine wraps outputs with confidence, threats, evidence, narrative, and next actions — never claiming certainty.

Phase 2+ will split engines further (video, document, network, identity, behavior, metadata) while keeping the same envelope.

## API versioning

All product APIs remain under `/api/v1/*`. OpenAPI available at `/docs` and `/openapi.json`.

## Deployment shapes

1. Local demo: `./scripts/run_demo.sh` (SQLite)
2. Docker Compose: `docker compose up --build` (Postgres + API)
3. Render: existing `Dockerfile` / `render.yaml` (set `DATABASE_URL` for durable Postgres)

## Next architecture phases

- Phase 2: Government analyst console + incident workflow states
- Phase 3: Modular AI engines + evidence vault
- Phase 4: National dashboards + regional analytics
- Phase 5: OIDC/MFA, partner APIs, hardened multi-tenant ops
