# MboaShield - Current Product Brief

**Date:** 16 July 2026  
**Version:** 0.7.0  
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

### Verification
- Text, impersonation, image, audio checks
- Multi-signal case analysis
- Explainable AI envelope (`ai_analysis`)

### Modular intelligence (Phase 3)
Independent engines:
- Text, Image, Audio, Identity, Source, Behavior, Network, Metadata (active)
- Video, Document (scaffolded, honest unsupported status)

Each engine returns confidence, evidence, reasoning, risk level, threat category,
and recommendations. Trust fusion produces an Explainable Trust Score and never
claims certainty.

### Government workflows (Phase 2)
National incident pipeline with timeline audit, analyst console, citizen dashboard,
institution admin.

### Platform foundation (Phase 1)
JWT/RBAC/audit, SQLAlchemy + Postgres path, Docker Compose, CI.

---

## 3. Key APIs

### Intelligence
- `GET /api/v1/intelligence/engines`
- `POST /api/v1/intelligence/analyze`
- `POST /api/v1/intelligence/analyze/media`
- `POST /api/v1/analyze` (now includes `engines` + `trust_score`)

### Detection / workflow / auth
All prior `/api/v1/check/*`, incidents, institutions, ambassadors, and auth routes
remain available.

---

## 4. Local run

```bash
./scripts/run_demo.sh
# http://127.0.0.1:8000
# Case panel shows Explainable Trust Score
```

Tests: **41 passing** at Phase 3 close.

---

## 5. Important files

- `backend/app/services/engines/`
- `backend/app/services/ai_analysis.py`
- `backend/app/api/v1/intelligence.py`
- `docs/PHASE_3_PLAN.md`
- `docs/ARCHITECTURE.md`
- `CHANGELOG.md`

---

## 6. Not yet complete

- Real neural deepfake / ONNX models behind adapters
- Full video and document pipelines (scaffolded only)
- National analytics / heat maps (Phase 4)
- OAuth2/OIDC + MFA (Phase 5)
- Evidence vault / object storage
- WhatsApp Business API

---

## 7. Next workstreams

### Phase 4 - National analytics
Threat trends, regional heat maps, response time, AI accuracy / false positives,
citizen participation metrics.

### Phase 5 - Hardened identity
OAuth2/OIDC, MFA, partner API keys.

---

## 8. Bottom line

MboaShield v0.7.0 is a national digital trust platform with modular explainable AI,
government incident workflows, and a production-oriented security chassis.
