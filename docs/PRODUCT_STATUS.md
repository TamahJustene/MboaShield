# MboaShield - Current Product Brief

**Date:** 16 July 2026  
**Version:** 0.8.0  
**Founder:** Justene Nkwagoh Tamah  
**Email:** tamahjustene45@gmail.com  
**Repo:** https://github.com/TamahJustene/MboaShield  
**Live app:** https://mboashield.onrender.com  

Use this file as the baseline when assigning the next work.

---

## 1. What MboaShield is

MboaShield is a Made-in-Cameroon National Digital Trust Platform for deepfakes,
disinformation, impersonation, voice-clone scams, and civic digital patriotism.

---

## 2. What works today

### Verification + modular intelligence
- Text/image/audio/impersonation checks
- Ten modular engines + Explainable Trust Score

### Government workflows
- National incident pipeline with timeline audit
- Analyst, citizen, and institution consoles

### National analytics (Phase 4)
- National Trust Dashboard
- Threat and deepfake trends
- Regional heat map
- Institution attack pressure
- Incident timeline and response time
- AI accuracy via analyst feedback labels
- Citizen participation metrics

### Platform foundation
- JWT/RBAC/audit, SQLAlchemy/Postgres path, Docker Compose, CI

---

## 3. Key analytics surfaces

| Surface | URL |
|---|---|
| National dashboard | `/static/national.html` |
| National API | `GET /api/v1/analytics/national` |
| Feedback labels | `POST /api/v1/analytics/feedback` |

---

## 4. Local run

```bash
./scripts/run_demo.sh
# http://127.0.0.1:8000/static/national.html
```

Tests: **45 passing** at Phase 4 close.

---

## 5. Important files

- `backend/app/services/analytics.py`
- `backend/app/api/v1/analytics.py`
- `frontend/static/national.html`
- `docs/PHASE_4_PLAN.md`
- `CHANGELOG.md`

---

## 6. Not yet complete

- OAuth2/OIDC + MFA (Phase 5)
- Real neural deepfake models
- Full video/document pipelines
- Evidence vault / object storage
- WhatsApp Business API
- External GIS map tiles

---

## 7. Next workstream

### Phase 5 - Hardened identity
OAuth2/OIDC readiness, MFA readiness, partner API keys, stronger production auth defaults.

---

## 8. Bottom line

MboaShield v0.8.0 adds national situational awareness on top of modular AI and
government incident workflows.
