# MboaShield - Current Product Brief

**Date:** 16 July 2026  
**Version:** 1.1.0  
**Founder:** Justene Nkwagoh Tamah  
**Email:** tamahjustene45@gmail.com  
**Repo:** https://github.com/TamahJustene/MboaShield  
**Live app:** https://mboashield.onrender.com  

**Start here** for what exists, who can use it, and how to change behaviour.  
For deeper maps see:

| Doc | Use when |
|---|---|
| [`ACCESS_AND_CONFIG.md`](ACCESS_AND_CONFIG.md) | Roles, who can call what, env knobs, promote users |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Layers, APIs, engines, workflow |
| [`DEPLOY.md`](DEPLOY.md) | Render / Vercel / local deploy |
| [`CHANGELOG.md`](../CHANGELOG.md) | Version history by phase |
| [`V1_0_ENTERPRISE_INDEX.md`](V1_0_ENTERPRISE_INDEX.md) | **v1.0 enterprise program** (review, design, threat model, roadmap) |
| [`PHASE_6_PLAN.md`](PHASE_6_PLAN.md) | Phase 6 identity completion notes |

---

## 1. What MboaShield is

Made-in-Cameroon **National Digital Trust Platform** for deepfakes, disinformation,
impersonation, voice-clone scams, and civic digital patriotism.

It is a working FastAPI + static frontend product: detection, national incident
workflow, modular AI engines, analytics, and enterprise identity � without
breaking the original pitch demo APIs.

---

## 2. What has been done (phases)

| Phase | Version | What shipped | How it was done |
|---|---|---|---|
| **1 Foundation** | 0.5.0 | SQLAlchemy (SQLite/Postgres), Alembic, JWT/RBAC/audit, middleware, Docker Compose, CI, `/api/v1` routers | App factory `create_app()`; repos over DB; soft auth so demo stays open |
| **2 Workflows** | 0.6.0 | National incident pipeline + timeline; analyst / citizen / institution consoles | State machine in `incident_workflow.py`; HTML operator UIs |
| **3 Modular AI** | 0.7.0 | 10 intelligence engines + Explainable Trust Score | Engine package + fusion in `trust_fusion.py`; `/api/v1/intelligence/*` |
| **4 Analytics** | 0.8.0 | National dashboard, trends, regions, feedback labels | `/api/v1/analytics/*` + `/static/national.html` |
| **5 Identity** | 0.9.0 | TOTP MFA, OIDC scaffolds, partner API keys | Auth/partners routers; hashed keys; `/static/identity.html` |
| **6 Enterprise Identity** | **1.0.0** | OIDC exchange, SAML SP, LDAP/AD, sessions, devices, password recovery, admin users, OAuth2 client credentials | Additive APIs + Alembic `0005`; feature flags; identity UI expanded |

All phases preserve existing `/api/v1/*` detection and demo flows.

---

## 3. Who can access what (summary)

**Default live/demo mode:** `AUTH_ENFORCE=false`  
Anyone with the URL can use citizen checks and most APIs **without login**.  
RBAC and API keys only apply when you turn enforcement on.

| Audience | Surfaces | Typical role |
|---|---|---|
| Public / jury | `/` Grand Jury demo, `/static/pitch.html` | none |
| Citizen | `/static/citizen.html`, `reports.html`, `history.html` | `citizen` |
| Analyst | `/static/analyst.html`, `national.html` | `analyst` |
| Institution | `/static/institutions.html` | `institution_admin` |
| Platform ops | `/static/identity.html` | `admin` |
| Partner systems | `X-API-Key` or OAuth2 client credentials | `partner` |

Register creates `citizen`. Promote via **Admin users API** or DB. See ACCESS_AND_CONFIG.

---

## 4. Current access mode on live

| Setting | Live Render (typical) | Meaning |
|---|---|---|
| `AUTH_ENFORCE` | `false` | Soft mode � gated routes do not 401/403 |
| `DEPLOYMENT_PROFILE` | `demo` (default) | Demo vs government warnings |
| `DATABASE_URL` | unset | SQLite (ephemeral on free tier) |
| `JWT_SECRET` | auto-generated | OK for demo; rotate for gov |

Government lock: Postgres + `AUTH_ENFORCE=true` + `MFA_ENFORCE=true` + promote admin + enable MFA.

---

## 5. Phase 6 identity surfaces

| Surface | Path |
|---|---|
| Identity UI | `/static/identity.html` |
| OIDC authorize/callback | `/api/v1/auth/oidc/*` |
| SAML metadata/ACS | `/api/v1/auth/saml/*` |
| LDAP login | `POST /api/v1/auth/ldap/login` |
| Sessions | `/api/v1/auth/sessions` |
| Trusted devices | `/api/v1/auth/devices` |
| Password forgot/reset | `/api/v1/auth/password/*` |
| Admin users | `/api/v1/admin/users` |
| OAuth2 clients/token | `/api/v1/oauth/*` |

---

## 6. Local run & tests

```bash
cd mboashield
./scripts/run_demo.sh
# http://127.0.0.1:8000/static/identity.html

source .venv/bin/activate
export PYTHONPATH=. JWT_SECRET=ci-test-secret
pytest backend/tests -q
```

---

## 7. Remaining gaps (post Phase 6)

Next per roadmap: **Phase 8 Threat Intelligence** (compliant sources only).

Still ahead: NTOC/cases, compliant threat intel, evidence vault, institution portal depth,
verified communications, advanced AI runtimes, Redis/queue/K8s, governance suite, full manuals.

---

## 8. Bottom line

**v1.1.0** adds the National Trust Operations Center on top of enterprise identity.
Demo profile stays open (`AUTH_ENFORCE=false`). Government profile is configuration-ready.
