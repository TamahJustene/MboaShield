# MboaShield Architecture

**Version:** 1.5.0 (Phase 11 verified communications)  
**Access / env adjustment:** [`ACCESS_AND_CONFIG.md`](ACCESS_AND_CONFIG.md)  
**Product status:** [`PRODUCT_STATUS.md`](PRODUCT_STATUS.md)

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

---

## 3. API surface (`/api/v1`)

Auth (MFA, OIDC, SAML, LDAP, sessions, devices, password), admin users, OAuth clients/token,
partners, intelligence, analytics, platform checks/incidents, government workflow,
NTOC/cases, intel, evidence vault, institution portal, verified announcements.

Root: `GET /health`, `GET /verify/a/{id}`, OpenAPI `/docs`.

---

## 4. Incident workflow

`open` → `ai_analysis` → `analyst_review` → `institution_review` → `decision` → `public_advisory` → `resolved` → `archived`  
Also: `dismissed`; legacy `reviewing` ≡ `analyst_review`.

---

## 5. Intelligence engines

8 active + 2 scaffolded (video, document). Product version 1.5.0; AI engine package version remains 0.9.0 until Phase 12.

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

SQLite default; Postgres via `DATABASE_URL`; Alembic 0001-0010; Render Docker demo; CI pytest.

---

## 8. Next

Phase 12 — Advanced AI Platform ([`V1_0_IMPLEMENTATION_ROADMAP.md`](V1_0_IMPLEMENTATION_ROADMAP.md)).
