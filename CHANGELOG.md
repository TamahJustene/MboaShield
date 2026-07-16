# Changelog

All notable changes to MboaShield are documented here.

## [0.6.0] - 2026-07-16

### Phase 2 — Government workflows

#### Added
- National incident workflow states with validated transitions
- Immutable `incident_events` timeline for every status change
- Auto AI-analysis stage when a report links a verification check
- Transition API: `POST /api/v1/incidents/{id}/transition`
- Timeline API: `GET /api/v1/incidents/{id}/timeline`
- Workflow blueprint: `GET /api/v1/workflow/states`
- Analyst queue + summary APIs and console UI (`/static/analyst.html`)
- Citizen dashboard API + UI (`/static/citizen.html`)
- Institution create/update admin APIs and registry admin UI
- Alembic migration `0002_phase2`

#### Changed
- Incident model extended with priority, region, assignment, institution, decision, advisory, AI summary
- Reports UI supports full workflow filters and timeline
- Version bumped to 0.6.0

#### Preserved
- Legacy statuses `open`, `reviewing`, `resolved`, `dismissed`
- Existing `/api/v1/incidents` create/list/get/patch contracts
- All Phase 1 auth/security and detection APIs

## [0.5.0] - 2026-07-16

### Phase 1 — Government platform foundation

#### Added
- Clean Architecture package layout: `core/`, `api/v1/`, `db/`
- SQLAlchemy ORM with SQLite default and PostgreSQL via `DATABASE_URL`
- Alembic migrations (`backend/alembic/versions/0001_phase1_initial.py`)
- JWT authentication with refresh tokens, password hashing, account lockout
- RBAC roles: `citizen`, `analyst`, `institution_admin`, `admin` (`AUTH_ENFORCE` soft-off by default)
- Immutable-style `audit_logs` table and writer
- Security middleware: request IDs, security headers, CORS, rate limiting
- Standardized error envelope for HTTP/App errors
- Docker Compose (`api` + `postgres`)
- GitHub Actions CI workflow
- Auth API: `/api/v1/auth/register|login|refresh|logout|me`
- Audit API: `GET /api/v1/audit/logs` (RBAC-gated when enforced)

#### Changed
- Application factory `create_app()` in `main.py`
- Repositories migrated from raw sqlite3 to SQLAlchemy
- Version bumped to 0.5.0
- Health endpoint reports database dialect and `auth_enforce`

#### Preserved
- All existing `/api/v1/*` detection, history, incident, ambassador, and institution APIs
- Legacy `X-MboaShield-User-Id` header
- Detector services and AI trust envelope contracts
- Static frontend surfaces

## [0.4.0] - 2026-07-16

- NLP text hybrid path, media/audio feature-model adapters
- Unified AI trust engine envelope
- Case analysis endpoint
- Incident reporting and history persistence
