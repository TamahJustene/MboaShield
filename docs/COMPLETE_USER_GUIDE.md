# MboaShield — Complete user and testing guide (v1.9.0)

**For:** Justene Nkwagoh Tamah and anyone demoing, testing, or auditing the platform.  
**Live demo:** https://mboashield.onrender.com  
**Navigation hub:** https://mboashield.onrender.com/static/hub.html  
**Presentation (PPT):** https://mboashield.onrender.com/static/presentations.html  
**How to explain to jury:** [`PRESENTER_GUIDE.md`](PRESENTER_GUIDE.md)

---

## 1. Before you start

| Item | Value |
|---|---|
| Product version | Check `/health` ? `"version":"1.9.0"` |
| Demo auth | `AUTH_ENFORCE=false` on Render (no login required for most UIs) |
| Database | SQLite on Render (resets if ephemeral disk clears) |
| Trust rule | All AI outputs use `certainty: "none"` unless a model card says otherwise |

**Wake Render:** Open `/health` once if the site slept (30–60s first load).

**Local:**

```bash
cd mboashield && ./scripts/run_demo.sh
# http://127.0.0.1:8000/static/hub.html
```

---

## 2. Master map — every screen

| # | Page | URL path | Primary role |
|---|---|---|---|
| 1 | Home / Grand Jury demo | `/` | Citizen, jury |
| 2 | Product hub | `/static/hub.html` | You (all links) |
| 3 | Presentation download | `/static/presentations.html` | Jury (PPT) |
| 4 | Citizen dashboard | `/static/citizen.html` | Citizen |
| 5 | Activity history | `/static/history.html` | Citizen |
| 6 | Incident reports | `/static/reports.html` | Citizen / analyst |
| 7 | Analyst console | `/static/analyst.html` | Analyst |
| 8 | National dashboard | `/static/national.html` | Government |
| 9 | NTOC | `/static/ntoc.html` | Operations |
| 10 | Intel | `/static/intel.html` | Analyst |
| 11 | Investigation | `/static/investigation.html` | Analyst |
| 12 | Institution registry | `/static/institutions.html` | Admin |
| 13 | Institution portal | `/static/institution-portal.html` | Institution admin |
| 14 | Announcements | `/static/announcements.html` | Publisher |
| 15 | Verify announcement | `/static/verify-announcement.html` | Public |
| 16 | Public verify API | `/verify/a/{id}` | Public |
| 17 | Identity | `/static/identity.html` | Admin |
| 18 | AI lab | `/static/ai-lab.html` | Admin / AI gov |
| 19 | Governance | `/static/governance.html` | AI gov / compliance |
| 20 | API docs | `/docs` | Developer |
| 21 | Health | `/health` | Ops |
| 22 | Metrics | `/metrics` | Ops (Prometheus) |

---

## 3. Grand Jury demo (home) — step by step

**URL:** `/`

### 3.1 Automated 90-second demo

1. Click **Run Grand Jury demo (90s)**.
2. Watch progress bar and checklist (5 scenarios).
3. **Pass:** Each step shows a risk band (LOW/MEDIUM/HIGH), explanation, and judge summary cards at bottom.
4. **Pass:** Finale section appears with impact stats and **Run demo again**.

### 3.2 Manual — Text rumour

1. Open panel **1 Text** (or nav chip).
2. Paste: `URGENT: Minister orders MoMo payment tonight to this number...`
3. Click **Analyse text**.
4. **Pass:** Score 0–100, band, reasons, advice, optional source verification block.
5. **API:** `POST /api/v1/check/text` JSON `{"text":"...","lang":"en"}`.

### 3.3 Manual — Impersonation

1. Panel **2 Identity**.
2. Name: `MINPOSTEL Official`; Handle: `@minpostel_urgent`
3. Click **Analyse account**.
4. **Pass:** Match or mismatch vs institution registry (17 institutions seeded).
5. **API:** `POST /api/v1/check/impersonation` `{"name":"...","handle":"..."}`.

### 3.4 Manual — Audio

1. Panel **3 Audio**.
2. Click **Sample voice** or upload `.wav`/`.mp3`.
3. Click **Analyse audio**.
4. **Pass:** Clone/synthetic risk signals and advice.
5. **API:** `POST /api/v1/check/audio` multipart `file`.

### 3.5 Manual — Image

1. Panel **4 Image**.
2. Use **Smooth face** sample or upload image.
3. Click **Analyse image**.
4. **Pass:** Media risk report.
5. **API:** `POST /api/v1/check/media` multipart `file`.

### 3.6 Manual — Mboa Ambassadors

1. Panel **5 Civic**.
2. Select a lesson, enter learner name.
3. Click **Get certificate**.
4. **Pass:** Certificate stub with ID.
5. **API:** `GET /api/v1/ambassadors/lessons`, `POST /api/v1/ambassadors/complete`.

### 3.7 AI case analysis

1. Panel **AI Case**.
2. Enter suspicious text + optional name/handle.
3. Click **Run AI case analysis**.
4. **Pass:** Trust fusion, `certainty: "none"`, optional `calibrated_score`.
5. **API:** `POST /api/v1/intelligence/analyze` or legacy `POST /api/v1/analyze`.

### 3.8 Language toggle

1. Click **FR** in header.
2. **Pass:** Panel titles switch EN/FR (partial i18n on home only).

---

## 4. Citizen journey

### 4.1 Citizen dashboard (`/static/citizen.html`)

1. Open page; optionally register user (creates local user via API).
2. **Pass:** Dashboard loads checks/history summary when user id in localStorage.
3. **API:** `GET /api/v1/citizen/dashboard`, `POST /api/v1/users`.

### 4.2 Activity history (`/static/history.html`)

1. Open after running checks on home.
2. Click a recent check row.
3. **Pass:** Detail view with signals and result JSON.
4. **API:** `GET /api/v1/checks/recent`, `GET /api/v1/checks/{id}`.

### 4.3 Report an incident (`/static/reports.html`)

1. Fill title, description, region (optional).
2. Submit new report.
3. **Pass:** Report appears in list with status `open`.
4. Open report ? view timeline.
5. Transition status (demo allows without login): e.g. `open` ? `ai_analysis` ? `analyst_review`.
6. **API:** `POST /api/v1/incidents`, `GET /api/v1/incidents`, `POST /api/v1/incidents/{id}/transition`.

**Important:** Public advisory requires human `decision` state first — never from AI alone.

---

## 5. Analyst and operations

### 5.1 Analyst console (`/static/analyst.html`)

1. Open page — summary and queue load.
2. Pick incident from queue; transition to next workflow state.
3. View timeline for an incident.
4. **Pass:** Summary counts update; transitions respect workflow rules.
5. **API:** `GET /api/v1/analyst/summary`, `GET /api/v1/analyst/queue`, transition same as reports.

### 5.2 National dashboard (`/static/national.html`)

1. Click **Refresh**.
2. **Pass:** Overview stats, threat trends, regional heat map, performance section.
3. Submit analyst feedback (if form present) for calibration pipeline.
4. **API:** `GET /api/v1/analytics/national`, `POST /api/v1/analytics/feedback`.

### 5.3 NTOC (`/static/ntoc.html`)

1. Open dashboard section.
2. **Pass:** Threat level, case counts, dashboard widgets.
3. Read notifications; mark read.
4. **API:** `GET /api/v1/ntoc/dashboard`, `GET /api/v1/notifications`.

### 5.4 Intel (`/static/intel.html`)

1. View source classes and sources list.
2. Add a demo source (partner webhook or RSS class per UI).
3. Click **Ingest** on a source (sync on Render).
4. **Pass:** Items list updates; correlate and national report buttons return JSON.
5. **API:** `/api/v1/intel/sources`, `POST .../ingest`, `POST /api/v1/intel/correlate`, `GET .../reports/national`.

### 5.5 Investigation (`/static/investigation.html`)

1. List cases; open workspace.
2. Create case; add note; assign (if UI enabled).
3. Register evidence link to case.
4. **API:** `/api/v1/cases/*`, `POST /api/v1/evidence`.

---

## 6. Institutions and verified communications

### 6.1 Registry (`/static/institutions.html`)

1. List 17 Cameroon institutions.
2. View detail by ID; create/update (demo mode).
3. **API:** `GET/POST/PATCH /api/v1/institutions`.

### 6.2 Institution portal (`/static/institution-portal.html`)

1. Select institution from dropdown.
2. View overview, domains, members, branding, official accounts, API keys.
3. Add domain / member / key (forms on page).
4. **API:** `/api/v1/institution-portal/{institution_id}/*`.

### 6.3 Announcements (`/static/announcements.html`)

1. Create draft announcement (title, body, institution).
2. Publish ? receive announcement id and verify URL.
3. **Pass:** Signature and version increment on republish.
4. **API:** `/api/v1/announcements/*`.

### 6.4 Public verify

1. **UI:** `/static/verify-announcement.html` — paste announcement id.
2. **API:** `GET /verify/a/{announcement_id}` — JSON authenticity payload.
3. **Pass:** `valid: true` for published signed content.

---

## 7. Identity, partners, admin (`/static/identity.html`)

Use when testing **hard auth** locally (`AUTH_ENFORCE=true`). On Render demo, many actions work without token.

| Action | Steps | API |
|---|---|---|
| Login | Email/password ? optional MFA | `POST /api/v1/auth/login`, MFA verify |
| MFA setup | Setup ? enable with TOTP code | `/api/v1/auth/mfa/*` |
| Sessions | List ? revoke one or all | `/api/v1/auth/sessions` |
| Trusted devices | List ? revoke | `/api/v1/auth/devices` |
| Admin users | Create user with role | `POST /api/v1/admin/users` |
| Partner API key | Create ? copy once | `POST /api/v1/partners/keys` |
| OAuth client | Create client credentials | `POST /api/v1/oauth/clients` |
| Password reset | Forgot ? reset token flow | `/api/v1/auth/password/*` |
| OIDC | List providers ? authorize URL | `/api/v1/auth/oidc/*` |

**Pass:** Security status panel shows MFA/OIDC readiness flags matching `/health` identity block.

---

## 8. AI platform (`/static/ai-lab.html`)

1. Page loads AI health (models count, calibration).
2. Click **Run EN golden evaluation** (and FR).
3. **Pass:** Metrics JSON: `cases`, `pass_rate`, `certainty: "none"`, latency within budget.
4. Optional curl:

```bash
curl -s https://mboashield.onrender.com/api/v1/ai-platform/health
curl -s -X POST https://mboashield.onrender.com/api/v1/ai-platform/evaluation/run \
  -H 'Content-Type: application/json' -d '{"dataset":"en"}'
```

5. Checksum verify: `GET /api/v1/ai-platform/models/mboashield-text-nlp-v1/verify-checksum` ? `"valid": true`.

---

## 9. Governance (`/static/governance.html`)

1. Health strip: risks, controls, cards counts.
2. Compliance snapshot JSON.
3. Risk register lines with `TM-*` threat refs.
4. Model cards list (`certainty=none`).
5. Consent demo: subject `demo-citizen`, feature `analytics_share`, **Grant** / **Revoke**.
6. **API:** `/api/v1/governance/health`, `/compliance`, `/risks`, `/consent` POST.

---

## 10. Infrastructure (operators)

| Check | Command / URL | Pass |
|---|---|---|
| Health | `GET /health` | `status: ok`, feature flags true |
| Metrics | `GET /metrics` | Prometheus text with `mboashield_` |
| Infra status | `GET /api/v1/infra/status` | version, redis, workers flags |
| Vault retention job | `POST /api/v1/infra/jobs/vault-retention?dry_run=true` | `mode: sync`, result count |
| Audit logs | `GET /api/v1/audit/logs` | recent privileged actions |

---

## 11. Incident workflow reference

```
open ? ai_analysis ? analyst_review ? institution_review ? decision
  ? public_advisory ? resolved ? archived
dismissed ? archived (from several states)
```

**Test invalid transition:** `POST transition` to illegal next state ? 400 error (when enforced).

---

## 12. Full regression checklist (printable)

Use before jury or after each deploy.

- [ ] `/health` version 1.9.0
- [ ] Home 90s demo completes 5/5
- [ ] Text / imp / audio / image manual checks
- [ ] Ambassador certificate
- [ ] AI case analysis returns `certainty: none`
- [ ] Create incident + one transition
- [ ] Analyst queue loads
- [ ] National analytics refresh
- [ ] NTOC dashboard
- [ ] Intel ingest (one source)
- [ ] Institution list (17)
- [ ] Publish announcement + verify URL
- [ ] AI lab EN eval pass_rate >= 0.5
- [ ] Governance risks >= 5
- [ ] Hub page health strip
- [ ] PPT downloads from `/static/presentations/MboaShield_SIN2026.pptx`
- [ ] `pytest backend/tests -q` (local / CI)

---

## 13. Automated tests (developers)

```bash
cd mboashield
source .venv/bin/activate
export PYTHONPATH=. JWT_SECRET=ci-test-secret
pytest backend/tests -q
```

Phase-specific: `test_phase12_ai.py`, `test_phase13_infra.py`, `test_phase14_governance.py`, `test_phase15_docs.py`.

---

## 14. Documents index

| Doc | Use |
|---|---|
| [`PRESENTER_GUIDE.md`](PRESENTER_GUIDE.md) | Jury / bootcamp speaking script |
| [`E2E_WALKTHROUGH.md`](E2E_WALKTHROUGH.md) | 25-min system tour |
| [`manuals/README.md`](manuals/README.md) | Role manuals for auditors |
| [`ACCESS_AND_CONFIG.md`](ACCESS_AND_CONFIG.md) | Env vars and RBAC |
| [`PITCH_DECK.md`](PITCH_DECK.md) | Legacy slide text (use PPT file for stage) |

---

## 15. Regenerate presentation

```bash
pip install python-pptx
python scripts/generate_presentation.py
```

Outputs:

- `docs/presentations/MboaShield_SIN2026.pptx`
- `frontend/static/presentations/MboaShield_SIN2026.pptx` (web download)

---

**Contact:** tamahjustene45@gmail.com · **Repo:** github.com/TamahJustene/MboaShield
