# MboaShield — Current Product Brief

**Date:** 16 July 2026  
**Version:** 0.5.0  
**Founder:** Justene Nkwagoh Tamah  
**Email:** tamahjustene45@gmail.com  
**Repo:** https://github.com/TamahJustene/MboaShield  
**Live app:** https://mboashield.onrender.com  

Use this file as the baseline when assigning the next work.

---

## 1. What MboaShield is

MboaShield is a **Made-in-Cameroon National Digital Trust Platform** built to protect citizens and institutions from:

- deepfakes / synthetic media
- WhatsApp disinformation and rumour panics
- institutional impersonation
- voice-clone scams
- digital identity abuse

It also includes a **digital patriotism / civic education** layer through **Mboa Ambassadors**.

**One-line positioning:**  
MboaShield is a sovereign AI shield for Cameroon's cyberspace — detection, explanation, escalation, and civic recovery in one product.

---

## 2. Product pillars

1. **Verification** — analyse suspicious text/claims and guide citizens
2. **Impersonation protection** — detect fake institutional accounts
3. **Synthetic media detection** — image and audio risk analysis
4. **Citizenship / Ambassadors** — lessons + certificates for digital patriotism
5. **Incident escalation** — report and review suspicious cases
6. **Trust engine layer** — AI analysis envelope with confidence, threats, evidence, and next actions
7. **Identity & governance (Phase 1)** — JWT auth, RBAC-ready roles, audit logs

---

## 3. What it can do today (capabilities)

### A. Citizen verification tools
- Analyse WhatsApp-style rumour text (FR/EN patterns)
- Check account name/handle for impersonation risk
- Analyse uploaded images for synthetic-media signals
- Analyse voice notes / audio for clone-risk signals
- Run a **multi-signal AI case analysis** (text + identity together)

### B. AI / intelligence layer
- Unified AI trust engine (`mboashield-trust-engine` v0.5.0)
- Every check returns risk score/band, confidence, threat categories, evidence, narrative, next actions
- Text uses **hybrid NLP + heuristics**
- Image/audio use **feature-model adapters** with heuristic fallback
- Honest posture: calibrated AI/heuristics with ML plug points (never claims certainty)

### C. Platform / product surfaces
- Mobile-first web app
- Grand Jury guided demo flow
- Activity history (stored checks + signals)
- Institution registry browser
- Incident reports queue (open ? reviewing ? resolved/dismissed)
- Lightweight user profiles + JWT auth endpoints
- Ambassador lessons + certificates
- Printable pitch deck page

### D. Persistence and auditability
- SQLAlchemy persistence (SQLite default, PostgreSQL via `DATABASE_URL`)
- Tables: verification checks/signals, institutions, users, certificates, incidents, audit logs, refresh tokens
- Alembic migration `0001_phase1`
- Checks can be linked via `X-MboaShield-User-Id` (legacy) or future JWT identity
- Audit logs for auth events and incident status updates

### E. Security foundation (Phase 1)
- JWT access + refresh tokens
- bcrypt password hashing
- Account lockout after failed logins
- RBAC roles (`citizen`, `analyst`, `institution_admin`, `admin`) — enforce with `AUTH_ENFORCE=true`
- Rate limiting, CORS, security headers, request IDs
- Standardized API error envelope

---

## 4. Live URLs

| Surface | URL |
|---|---|
| Home / demo | https://mboashield.onrender.com/ |
| Health | https://mboashield.onrender.com/health |
| Activity history | https://mboashield.onrender.com/static/history.html |
| Incident reports | https://mboashield.onrender.com/static/reports.html |
| Institution registry | https://mboashield.onrender.com/static/institutions.html |
| Pitch deck | https://mboashield.onrender.com/static/pitch.html |
| API docs | https://mboashield.onrender.com/docs |

Local run:

```bash
cd mboashield
./scripts/run_demo.sh
# http://127.0.0.1:8000

# Production-like:
docker compose up --build
```

---

## 5. API map (current)

### Health / platform
- `GET /health`
- `POST /api/v1/users`
- `GET /api/v1/users/{user_id}`
- `GET /api/v1/institutions`
- `GET /api/v1/institutions/{institution_id}`

### Auth (Phase 1)
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

### Detection
- `POST /api/v1/check/text`
- `POST /api/v1/check/impersonation`
- `POST /api/v1/check/media`
- `POST /api/v1/check/audio`
- `POST /api/v1/analyze`

### History
- `GET /api/v1/checks/recent`
- `GET /api/v1/checks/{check_id}`
- `GET /api/v1/certificates/recent`
- `GET /api/v1/certificates/{certificate_id}`

### Incidents
- `POST /api/v1/incidents`
- `GET /api/v1/incidents`
- `GET /api/v1/incidents/{report_id}`
- `PATCH /api/v1/incidents/{report_id}`

### Ambassadors
- `GET /api/v1/ambassadors/lessons`
- `POST /api/v1/ambassadors/complete`

### Audit
- `GET /api/v1/audit/logs`

---

## 6. Tech stack

- **Backend:** FastAPI + Python 3.12 + SQLAlchemy 2 + Alembic
- **Frontend:** static HTML/CSS/JS (mobile-first)
- **DB:** SQLite (default) / PostgreSQL (production-ready)
- **Auth:** JWT + refresh tokens + passlib/bcrypt
- **Deploy:** Docker, Docker Compose, Render (`render.yaml`), GitHub Actions CI
- **Tests:** pytest (30 passing at Phase 1 close)
- **AI engines:** trust engine, text NLP v1, media/audio adapters

---

## 7. Important product files

### Core backend
- `backend/app/main.py` — app factory
- `backend/app/api/v1/` — versioned routers
- `backend/app/core/` — config, security, RBAC, middleware, errors
- `backend/app/db/` — SQLAlchemy models + session
- `backend/app/repositories.py` — persistence service layer
- `backend/app/schemas.py` — typed request/response models
- `backend/app/services/*` — detectors + AI trust engine

### Ops
- `docker-compose.yml`
- `alembic.ini` + `backend/alembic/`
- `.env.example`
- `.github/workflows/ci.yml`
- `CHANGELOG.md`

### Docs
- `docs/ARCHITECTURE.md`
- `docs/PHASE_1_AUDIT.md`
- `docs/DEPLOY.md`
- `docs/DATA_MODEL_V1.md`

---

## 8. Current maturity (honest)

### Strong today
- Working multimodal verification product
- Explainable AI analysis contract
- Persistence + history + incidents
- Institution registry
- Phase 1 security/auth/audit foundation
- PostgreSQL-ready data layer
- Deployed live demo
- Competition/dossier packaging already submitted

### Not yet production-complete
- AUTH_ENFORCE defaults soft (demo continuity); turn on for government deploy
- OAuth2/OIDC and MFA UI not implemented
- No real deep neural deepfake model yet (adapters are feature-model + heuristic fallback)
- Government analyst console / national dashboards not built
- No WhatsApp Business API integration yet
- No object storage / evidence vault yet
- Render free tier still needs managed Postgres for durable production data

---

## 9. Competition context

- Event: MINPOSTEL SIN 2026 / ICT Innovation Week
- Theme alignment: protect cyberspace from AI excesses + digital patriotism
- Dossier submitted
- Live demo URL in use: `https://mboashield.onrender.com`

---

## 10. Recommended next workstreams (Phase 2+)

### Phase 2 — Government workflows
- National incident workflow states (citizen ? AI ? analyst ? institution ? advisory ? resolved ? archived)
- Analyst console UI
- Institution administration portal
- Citizen dashboard

### Phase 3 — AI modularization
- Independent engines: text, image, audio, video, identity, document, network, source, behavior, metadata
- Combined Explainable Trust Score

### Phase 4 — National analytics
- Threat trends, regional heat maps, response time, AI accuracy metrics
- Verification certificates for official announcements

### Phase 5 — Hardened identity
- OAuth2 / OIDC providers
- MFA
- Partner API keys

---

## 11. How to assign next tasks

- "Continue from PRODUCT_STATUS.md — implement Phase 2 analyst console"
- "Next: expand incident workflow states with full audit trail"
- "Next: plug a real ONNX image model into model_adapters.py"

Always assume this file is the source of truth for **current state**.

---

## 12. Bottom line

MboaShield v0.5.0 is the **Phase 1 foundation** of a national digital trust platform:

- multimodal detection preserved
- AI explanation layer preserved
- durable ORM + Postgres path
- JWT/RBAC/audit security chassis
- Docker Compose + CI
- all prior citizen features still working

Next phases deepen **government workflows**, **modular AI**, and **national analytics** on this chassis.
