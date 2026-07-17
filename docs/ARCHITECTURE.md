# MboaShield Architecture

**Version:** 2.0.0 (baseline) · **2030 program:** [`MBOASHIELD_2030_INDEX.md`](MBOASHIELD_2030_INDEX.md) · **T0:** [`PHASE_T0_PLAN.md`](PHASE_T0_PLAN.md)  
**Access / env:** [`ACCESS_AND_CONFIG.md`](ACCESS_AND_CONFIG.md)  
**Product status:** [`PRODUCT_STATUS.md`](PRODUCT_STATUS.md)

---

## 0. National platforms (2030 view)

The same codebase is organized into **ten national platforms**. See [`pillars/PILLAR_REGISTRY.md`](pillars/PILLAR_REGISTRY.md).

| Platform | Primary API areas (v1) |
|---|---|
| Trust | `/check/*`, `/intelligence/*` → future `/trust/*` |
| Identity | `/auth/*`, `/admin/users`, OIDC/SAML/LDAP |
| Threat intelligence | `/intel/*` |
| Investigation | `/cases/*`, `/incidents/*`, government workflow |
| Evidence | `/evidence/*` |
| Government communications | `/announcements/*`, `/verify/a/*` |
| Analytics | `/analytics/*` |
| AI | `/ai-platform/*` |
| Governance | `/governance/*` |
| Partner | `/partners/*`, `/oauth/*` |

Transformation roadmap: [`NATIONAL_INFRASTRUCTURE_TRANSFORMATION_PLAN.md`](NATIONAL_INFRASTRUCTURE_TRANSFORMATION_PLAN.md).

---

## 1. Stack overview

```text
Browser / IdP / LDAP / Partner systems
        |
        +-- Static UI (/ and /static/*)
        +-- JWT bearer + sessions
        +-- MFA challenge (TOTP) + trusted devices
        +-- OIDC code exchange / SAML ACS / LDAP bind
        +-- X-API-Key + OAuth2 client_credentials
        v
FastAPI create_app()          backend/app/main.py
        |
        +-- middleware (CORS, rate limit, security headers)
        +-- GET /health
        +-- /api/v1/* routers (auth, ntoc, intel, evidence, ...)
        +-- /static/*  -> frontend/
        v
Services + stores + repositories
        |
        +-- engines/* + trust fusion
        +-- incident_workflow + ntoc
        +-- intel connectors (compliant only)
        +-- vault storage + signing
        +-- identity_federation (OIDC/SAML/LDAP)
        v
SQLAlchemy (SQLite or PostgreSQL)
Alembic migrations 0001-0008
Object storage: local FS (demo) or S3 (gov)
```

---

## 2. How phases layer

| Layer | Package / area | Responsibility |
|---|---|---|
| Chassis | `core/`, `db/`, `api/deps.py` | Config, RBAC, JWT, DB session, soft/hard auth |
| Platform | `api/v1/platform.py` | Checks, analyze, users, institutions, ambassadors, audit |
| Government | `api/v1/government.py` | Workflow, analyst/citizen/institution consoles |
| Intelligence | `api/v1/intelligence.py`, `services/engines/` | 10 engines + analyze |
| Analytics | `api/v1/analytics.py` | National aggregates + feedback |
| Identity | `auth.py`, `admin_users.py`, `oauth.py`, `partners.py` | Enterprise identity + partners |
| NTOC | `cases.py`, `ntoc.py`, `ntoc_store` | Cases, threat level, notifications |
| Intel | `intel.py`, `services/intel/`, `intel_store` | Compliant sources, correlate, reports |
| Vault | `evidence.py`, `services/vault/`, `vault_store` | Hash, custody, export, retention |
| Institution portal | `institution_portal.py`, `institution_store` | Domains, members, branding, `msi_` keys |
| Verified comms | `announcements.py`, `public_verify.py`, `announcement_store` | Signed announcements + `/verify/a/*` |
| Advanced AI | `ai_platform.py`, `ai_store`, `services/ai/` | Registry, calibration, golden eval, adapters |
| Infrastructure | `infra.py`, `workers/`, `core/metrics.py` | Metrics, Celery jobs, gov compose / Helm |
| Governance | `governance.py`, `governance_store` | Consent, risk register, model/dataset cards |

---

## 3. API surface (`/api/v1`)

Auth (MFA, OIDC, SAML, LDAP, sessions, devices, password), admin users, OAuth clients/token,
partners, intelligence, analytics, platform checks/incidents, government workflow,
NTOC/cases, intel, evidence vault, institution portal, verified announcements, AI platform (`/api/v1/ai-platform/*`), infra (`/api/v1/infra/*`), governance (`/api/v1/governance/*`).

Root: `GET /health`, `GET /metrics`, `GET /verify/a/{id}`, OpenAPI `/docs`.

---

## 4. Incident workflow

`open` → `ai_analysis` → `analyst_review` → `institution_review` → `decision` → `public_advisory` → `resolved` → `archived`  
Also: `dismissed`; legacy `reviewing` ≡ `analyst_review`.

---

## 5. Intelligence engines

8 active + 2 scaffolded (video, document). Product version 1.6.0; trust engine package **1.2.0** with optional calibration (`calibrated_score`); certainty remains `"none"`.

---

## 6. Identity controls (Phase 6)

- Local password + lockout + configurable policy
- TOTP MFA + trusted devices + optional MFA enforce
- OIDC code exchange, SAML SP, LDAP/AD
- Sessions registry + revoke
- Password recovery tokens
- Admin user management
- Partner API keys + OAuth2 client credentials
- Deployment profile warnings for government/production

---

## 7. Data & deploy

Alembic 0001-0014; Render Docker demo; `docker-compose.gov.yml`; Helm `deploy/helm/mboashield`; CI pytest.

---

## 8. Next

**MboaShield 2030:** Execute transformation phase T0 per [`NATIONAL_INFRASTRUCTURE_TRANSFORMATION_PLAN.md`](NATIONAL_INFRASTRUCTURE_TRANSFORMATION_PLAN.md).  
Operational testing today: [`COMPLETE_USER_GUIDE.md`](COMPLETE_USER_GUIDE.md).
