# MboaShield - Current Product Brief

**Date:** 16 July 2026  
**Version:** 1.4.0  
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
| [`V1_0_ENTERPRISE_INDEX.md`](V1_0_ENTERPRISE_INDEX.md) | **v1.0 enterprise program** |
| [`PHASE_10_PLAN.md`](PHASE_10_PLAN.md) | Phase 10 institution portal notes |

---

## 1. What MboaShield is

Made-in-Cameroon **National Digital Trust Platform** for deepfakes, disinformation,
impersonation, voice-clone scams, and civic digital patriotism.

Working FastAPI + static frontend: detection, national incident workflow, modular AI,
analytics, enterprise identity, NTOC, compliant threat intelligence, evidence vault,
and institution administration — without breaking original pitch demo APIs.

---

## 2. What has been done (phases)

| Phase | Version | What shipped |
|---|---|---|
| 1–5 | 0.5–0.9 | Foundation through MFA / partner keys |
| **6 Enterprise Identity** | 1.0.0 | OIDC, SAML, LDAP, sessions, admin users |
| **7 NTOC** | 1.1.0 | Cases, threat level, notifications |
| **8 Threat Intel** | 1.2.0 | Compliant sources, correlation, reports |
| **9 Evidence Vault** | 1.3.0 | Hashing, custody, signed exports, retention |
| **10 Institution Portal** | **1.4.0** | Domains, memberships, branding, `msi_` keys, portal UI |

---

## 3. Who can access what (summary)

**Default live/demo mode:** `AUTH_ENFORCE=false` — most APIs open without login.

| Audience | Surfaces | Typical role |
|---|---|---|
| Institution ops | `/static/institutions.html`, `/static/institution-portal.html` | `institution_admin` |
| Analyst | NTOC / intel / investigation | `analyst` |
| Platform ops | `/static/identity.html` | `admin` |

---

## 4. Phase 10 surfaces

| Surface | Path |
|---|---|
| Portal UI | `/static/institution-portal.html` |
| Portal APIs | `/api/v1/institution-portal/{institution_id}/*` |
| Institution keys | `msi_...` via `X-API-Key` |

---

## 5. Local run & tests

```bash
cd mboashield
./scripts/run_demo.sh
# http://127.0.0.1:8000/static/institution-portal.html

source .venv/bin/activate
export PYTHONPATH=. JWT_SECRET=ci-test-secret
pytest backend/tests -q
```

---

## 6. Remaining gaps

Next: **Phase 11 Verified Government Communications**.

Still ahead: verified announcements, advanced AI runtimes, Redis/queue/K8s, governance, manuals.

---

## 7. Bottom line

**v1.4.0** adds the Institution Administration Portal on top of vault, intel, NTOC, and identity.
Demo profile stays open (`AUTH_ENFORCE=false`).
