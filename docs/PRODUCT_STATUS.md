# MboaShield - Current Product Brief

**Date:** 16 July 2026  
**Version:** 0.9.0  
**Founder:** Justene Nkwagoh Tamah  
**Email:** tamahjustene45@gmail.com  
**Repo:** https://github.com/TamahJustene/MboaShield  
**Live app:** https://mboashield.onrender.com  

Use this file as the baseline when assigning the next work.

---

## 1. What MboaShield is

Made-in-Cameroon National Digital Trust Platform for deepfakes, disinformation,
impersonation, voice-clone scams, and civic digital patriotism.

---

## 2. Completed platform phases

1. Foundation - SQLAlchemy/Postgres, JWT/RBAC/audit, Docker/CI
2. Government workflows - national incident pipeline + operator consoles
3. Modular AI - 10 engines + Explainable Trust Score
4. National analytics - dashboard, trends, heat map, feedback labels
5. Hardened identity - MFA, OIDC readiness, partner API keys

---

## 3. Phase 5 identity surfaces

| Surface | Path |
|---|---|
| Identity UI | `/static/identity.html` |
| Security status | `GET /api/v1/auth/security-status` |
| MFA setup/enable/verify | `/api/v1/auth/mfa/*` |
| OIDC providers | `GET /api/v1/auth/oidc/providers` |
| Partner API keys | `/api/v1/partners/keys` |
| Partner identity | `GET /api/v1/partners/me` (`X-API-Key`) |

Production guidance: set strong `JWT_SECRET`, `AUTH_ENFORCE=true`, configure OIDC
env vars, and issue scoped partner keys.

---

## 4. Local run

```bash
./scripts/run_demo.sh
# http://127.0.0.1:8000/static/identity.html
```

Tests: green at Phase 5 close.

---

## 5. Remaining product gaps (post Phase 5)

- Live national IdP token exchange (config-ready scaffold exists)
- Real neural deepfake models / full video-document pipelines
- Evidence vault / object storage
- WhatsApp Business API
- External GIS map tiles

---

## 6. Bottom line

MboaShield v0.9.0 is a government-oriented digital trust platform with detection,
workflow, analytics, and hardened identity controls suitable for continued
national deployment hardening.
