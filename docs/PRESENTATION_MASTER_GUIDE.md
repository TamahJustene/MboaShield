# MboaShield presentation master guide

**Current release:** v2.8.0  -  MboaShield 2030 T0-T7 complete  -  CI-1
**Founder:** Justene Nkwagoh Tamah
**Live platform:** https://mboashield.onrender.com
**Presenter command center:** https://mboashield.onrender.com/static/hub.html
**Slide deck:** https://mboashield.onrender.com/static/presentations.html

This is the single guide to use before and during a presentation. It explains what to open, what every screen does, where each feature lives in the repository, which API powers it, and what to say.

---

## 1. The product in one sentence

MboaShield is a Made-in-Cameroon national digital trust platform that helps citizens assess suspicious content and identities, gives institutions a controlled response network, and is designed for high-impact decisions to remain under human review.

## 2. The three truths to communicate

1. **Citizen value:** A person can check a rumour, suspicious account, voice note, or image and receive an explainable risk/trust assessment.
2. **National workflow:** A suspicious item can become an incident and move through analyst, institution, decision, and advisory states. Hard authentication and operating procedures are required to enforce human accountability in production.
3. **Infrastructure depth:** The same platform includes identity, institution trust relationships, signed announcements, intelligence exchange, governance, interoperability, country packs, and operations tooling.

Never claim that an automated score is forensic proof. MboaShield deliberately returns `certainty: "none"` for automated trust assessments.

---

## 3. Presentation-day command center

Open these tabs in this exact order before the jury enters:

| Tab | URL | Why it is open |
|---|---|---|
| 1 | `/health` | Confirms the live release is awake and healthy |
| 2 | `/` | Main 90-second citizen demo |
| 3 | `/static/hub.html` | One-click access to every product surface |
| 4 | `/static/analyst.html` | Human review and incident workflow |
| 5 | `/static/ntoc.html` | National operations view |
| 6 | `/static/announcements.html` | Signed government communications |
| 7 | `/static/governance.html` | Responsible-AI proof |
| 8 | `/docs` | Technical proof if an expert asks |
| 9 | `/static/presentations.html` | Downloadable PowerPoint backup |

### Live deployment facts

The public Render deployment is intentionally a demonstration profile:

| Item | Live demo |
|---|---|
| Authentication | Soft (`AUTH_ENFORCE=false`) |
| Database | SQLite |
| Workers | Off; synchronous fallback |
| Country pack | Cameroon (`cm`) |
| Languages | Partial English/French UI: home titles and shared navigation chrome |
| Target national profile | Hard-auth defaults, MFA, Postgres, workers, and secret injection; route authorization and tenant isolation still require completion and audit |

Do not describe the free Render profile as the final government production topology.

---

## 4. Perfect three-minute presentation flow

### 0:00-0:20 - Problem

> "Cameroonians receive fake minister messages, cloned voice notes, fraudulent mobile-money instructions, and manipulated images every day. The problem is not only detection; it is the loss of trust between citizens and institutions."

Show slide 1 or the home header. Do not open technical pages yet.

### 0:20-0:35 - Solution

> "MboaShield is a sovereign digital trust platform: it detects, explains, escalates, verifies, and educates using local institutional context and a human-review workflow."

Point to the five items in the home demo checklist.

### 0:35-2:05 - Live citizen demo

Open `/` and click **Run Grand Jury demo (90s)**.

Say one sentence per step:

1. **Text:** "A viral rumour receives a risk score, reasons, trusted-source guidance, and a national trust assessment."
2. **Identity:** "A suspicious authority-style account is compared against Cameroon's institution registry."
3. **Audio:** "A voice note is screened for cloned-voice risk signals."
4. **Image:** "A suspicious image receives synthetic-media signals in plain language."
5. **Civic:** "The journey ends with digital education and an Mboa Ambassador certificate."

Do not wait silently while a request runs. Explain the story and the intended human-review policy.

### 2:05-2:30 - Show national depth

Open `/static/hub.html`, then click **Analyst** or **NTOC**.

> "This is not a checker alone. A risky item can enter an incident workflow, be reviewed by analysts and institutions, preserve evidence, and progress toward a public advisory. In production, hard authentication and operating controls must enforce the human decision policy."

### 2:30-2:45 - Responsible AI

Open `/static/governance.html`.

> "MboaShield never presents AI confidence as absolute truth. Its governance portal exposes model cards, risks, consent, and controls. The framework-map API maps controls to ISO/NIST identifiers without claiming certification."

### 2:45-3:00 - Impact and ask

> "Citizens receive free protection; schools receive digital-patriotism education; banks, telecoms, media, and government receive trusted APIs and workflows. I am asking for support to move from a working national prototype to durable, independently audited public infrastructure."

Close with:

> "MboaShield is not adjacent to the theme-MboaShield is the theme."

---

## 5. Every UI screen: purpose, location, and backend

All browser pages are in `frontend/` and are served by `backend/app/main.py`.

| Screen | Live path | Audience / purpose | Frontend source | Main backend |
|---|---|---|---|---|
| Grand Jury home | `/` | Citizen demo: text, identity, audio, image, civic learning | `frontend/index.html`, `frontend/static/app.js` | `api/v1/trust.py`, `api/v1/platform.py` |
| Product hub | `/static/hub.html` | Presenter command center | `frontend/static/hub.html`, `hub.js` | `/health`, `/api/v1/program` |
| Presentations | `/static/presentations.html` | Download PowerPoint | `frontend/static/presentations.html` | Static file |
| Pitch page | `/static/pitch.html` | Browser pitch summary | `pitch.html` | Static page |
| Citizen dashboard | `/static/citizen.html` | Personal checks, incidents, certificates | `citizen.html`, `citizen.js` | `api/v1/platform.py`, `government.py` |
| Activity history | `/static/history.html` | Stored checks and evidence signals | `history.html`, `history.js` | `api/v1/platform.py` |
| Incident reports | `/static/reports.html` | File and track an incident | `reports.html`, `reports.js` | `api/v1/platform.py`, `government.py` |
| Analyst console | `/static/analyst.html` | Review queue and transition workflow | `analyst.html`, `analyst.js` | `api/v1/government.py` |
| National dashboard | `/static/national.html` | Aggregates, trends, regions, feedback | `national.html`, `national.js` | `api/v1/analytics.py` |
| NTOC | `/static/ntoc.html` | Threat level, notifications, operational queue | `ntoc.html`, `ntoc.js` | `api/v1/ntoc.py` |
| Threat intelligence | `/static/intel.html` | Compliant feeds and partner ingest | `intel.html`, `intel.js` | `api/v1/intel.py` |
| Investigation | `/static/investigation.html` | Cases, notes, assignments, evidence | `investigation.html`, `investigation.js` | `api/v1/cases.py`, `evidence.py` |
| Institution registry | `/static/institutions.html` | Official institution records | `institutions.html`, `institutions.js` | `api/v1/platform.py`, `government.py` |
| Institution portal | `/static/institution-portal.html` | Domains, members, keys, partners, alerts | `institution-portal.html`, `institution-portal.js` | `api/v1/platform.py`, `institution_portal.py`, `trust_network.py` |
| Announcements | `/static/announcements.html` | Draft, publish, revoke signed messages | `announcements.html`, `announcements.js` | `api/v1/platform.py`, `announcements.py` |
| Public verification | `/static/verify-announcement.html` | Verify an announcement signature | `verify-announcement.html`, `verify-announcement.js` | `api/public_verify.py` |
| Identity & MFA | `/static/identity.html` | Login, MFA, users, keys, OAuth | `identity.html`, `identity.js` | `api/v1/auth.py`, `admin_users.py`, `oauth.py`, `partners.py` |
| AI lab | `/static/ai-lab.html` | Models, checksums, evaluation, calibration | `ai-lab.html`, `ai-lab.js` | `api/v1/ai_platform.py` |
| Governance | `/static/governance.html` | Risks, controls, cards, consent | `governance.html`, `governance.js` | `api/v1/governance.py` |
| Developer portal | `/static/developer.html` | OpenAPI, keys, webhooks, STIX/CAP/TAXII | `developer.html`, `developer.js` | `api/v1/platform.py`, `partners.py`; documents `interop.py`, `taxii.py`, `scim.py` |
| Sector modules | `/static/sectors.html` | Election, health, finance toggles | `sectors.html`, `sectors.js` | `/api/v1/sectors`, `/api/v1/country-pack` in `platform.py` |
| OpenAPI | `/docs` | Interactive technical contract | Generated by FastAPI | All `api/v1` routers |
| ReDoc | `/redoc` | Readable API reference | Generated by FastAPI | All `api/v1` routers |
| Health | `/health` | Release and capability truth | - | `backend/app/main.py` |
| Metrics | `/metrics` | Prometheus metrics | - | Registered in `main.py`; implemented by `core/metrics.py` |

### Shared portal shell

`frontend/static/portal-shell.js` provides common navigation, tenant identity, release/phase context, auth awareness, and EN/FR navigation chrome for operational portals. Most portal body content is not yet translated.

---

## 6. Feature map by national platform pillar

| Pillar | What to show | Main API | Main implementation |
|---|---|---|---|
| Trust | Home trust panel | `/api/v1/trust/*` | `services/trust_assessment.py`, `trust_store.py` |
| Identity | Identity page, SCIM | `/api/v1/auth/*`, `/scim/v2/*` | `identity_store.py`, `api/v1/scim.py` |
| Threat intelligence | Intel page, TAXII | `/api/v1/intel/*`, `/taxii2/*` | `intel_store.py`, `services/interop/stix_export.py` |
| Investigation | Analyst/investigation | `/api/v1/cases/*`, `/api/v1/incidents/*` | `ntoc_store.py`, `incident_workflow.py` |
| Evidence | Evidence vault APIs | `/api/v1/evidence/*` | `vault_store.py` |
| Government communications | Announcement + public verify | `/api/v1/announcements/*`, `/verify/a/*` | `announcement_store.py` |
| Analytics | National dashboard | `/api/v1/analytics/*` | `services/analytics.py` |
| AI | AI lab | `/api/v1/ai-platform/*` | `ai_store.py`, `services/ai/*` |
| Governance | Governance page | `/api/v1/governance/*` | `governance_store.py` |
| Partner / trust network | Institution portal, developer portal | `/api/v1/trust-network/*`, `/api/v1/interop/*` | `trust_network_store.py`, `interop_store.py` |
| Infrastructure | Health, metrics, resilience | `/health`, `/metrics`, `/api/v1/infra/*` | `core/metrics.py`, `workers/` |

---

## 7. The most important end-to-end workflow

```text
Citizen checks suspicious content
    |
TrustAssessment is stored with score, band, signals, certainty=none
    |
Citizen files an incident (optional)
    |
    +--> AI analysis (optional) --> Analyst review
    +-----------------------------> Analyst review

Analyst review --> Decision
Analyst review --> Institution review --> Decision

Decision --> Resolved --> archived
Decision --> Public advisory --> Resolved --> archived
National analytics and audit records
```

The workflow truth lives in `backend/app/services/incident_workflow.py`.

Transition ordering is enforced in code, but the demo's soft-auth profile does not prove who performed a transition. The presentation must describe human review as the operating policy; national production requires hard authentication, role procedures, and audit oversight.

---

## 8. Repository map: where everything is placed

| Folder / file | Contains |
|---|---|
| `backend/app/main.py` | FastAPI application, health, static serving |
| `backend/app/api/v1/` | Versioned API route modules |
| `backend/app/core/` | Config, security, RBAC, metrics, OpenAPI pillars |
| `backend/app/services/` | Detection, trust, interop, workflow logic |
| `backend/app/db/models.py` | SQLAlchemy persistence models |
| `backend/app/*_store.py` | Domain persistence operations |
| `backend/alembic/versions/` | Database migrations |
| `backend/tests/` | Automated API and phase tests |
| `frontend/index.html` | Main competition/citizen demo |
| `frontend/static/*.html` | Product portals |
| `frontend/static/*.js` | Page behavior and API calls |
| `frontend/static/styles.css` | Shared visual system |
| `frontend/static/samples/` | Demo image/audio assets |
| `frontend/static/presentations/` | Web-downloadable PowerPoint |
| `data/` | Institution and AI golden-set seed data |
| `deploy/country-packs/` | Cameroon and reusable country-pack definitions |
| `deploy/helm/` | Kubernetes chart |
| `deploy/profiles/national.env` | National hard-auth deployment template |
| `deploy/sql/rls_tenant.sql` | Fail-closed Postgres RLS activation template; waits for tenant columns/backfill |
| `docs/` | Product, operations, architecture, presentation guides |
| `scripts/generate_presentation.py` | Generates the PowerPoint |
| `scripts/load/` | Locust and k6 load scenarios |
| `Dockerfile`, `render.yaml` | Container and Render deployment |

---

## 9. What to open when the jury asks

| Question | Open | Answer focus |
|---|---|---|
| "Show the citizen benefit." | `/` | Explainable multimodal checks |
| "Where is the human?" | `/static/analyst.html` | Review workflow and timeline; complete route authorization plus operating controls are still required |
| "How does government see threats?" | `/static/ntoc.html` | Threat level and operational queue |
| "How do institutions collaborate?" | `/static/institution-portal.html` | Trusted partners and shared alerts |
| "Can an official message be verified?" | Announcements + public verify | Signature, version, revocation |
| "Is the AI responsible?" | `/static/governance.html` | Certainty policy, risks, cards, controls |
| "Can other systems integrate?" | `/static/developer.html`, `/docs` | OpenAPI, webhooks, STIX, CAP, TAXII, SCIM |
| "Can it scale?" | `/api/v1/infra/resilience` | Load, HA, DR patterns and targets; measured production proof is future work |
| "Can another country use it?" | `/api/v1/country-pack` | Country configuration without rewrite |
| "Where is the code?" | GitHub + `/docs` | Pillar-based modular monolith |

---

## 10. Honest answers to difficult questions

### "Is the deepfake model production-grade?"

> "The current public prototype uses explainable heuristics and model adapters. MboaShield does not claim forensic proof. Production models must be checksum-registered, evaluated, governed, and remain subject to human review."

### "Is this already government production?"

> "The public Render instance is a working demonstration profile. The repository includes hardened deployment templates, Postgres/Helm patterns, MFA, fail-closed RLS guidance, KMS guidance, load scripts, and a DR runbook. Complete route authorization, tenant columns, measured drills, and independent security/legal audits remain required before national production."

### "Are you ISO/NIST certified?"

> "No. Governance controls are mapped to ISO 27001 and NIST CSF identifiers so they can be assessed. Certification requires an independent audit."

### "Why not use an international platform?"

> "MboaShield combines local institution identity, a partially translated French/English citizen experience, a sovereign-deployment path, national workflows, digital-patriotism education, and standard integration APIs."

### "What happens to citizen data?"

> "The design minimizes personal data, supports consent, role-based access, retention, evidence custody, audit logs, and a national KMS/secret-management pattern. The demo database is not the final national data architecture."

---

## 11. UI/UX presentation rules

1. Use the **home page first**. Never begin with Swagger or architecture.
2. Keep browser zoom at 100% and presentation resolution at 16:9.
3. Do not rapidly switch among all portals; use the hub as the transition.
4. Narrate the user outcome, not the button click.
5. Use one high-risk sample that has been tested before the event.
6. Keep the language toggle on English unless the jury requests French.
7. Show only one technical proof page unless asked.
8. Never expose API keys, temporary passwords, JWTs, `.env`, or raw secrets.
9. If a page is empty, explain that data is generated by the workflow-do not improvise fake production statistics.
10. End on impact and the ask, not on logs or JSON.

---

## 12. Pre-presentation verification checklist

Run this 30-60 minutes before presenting:

- [ ] Open `https://mboashield.onrender.com/health`.
- [ ] Confirm `status=ok`, `version=2.8.0`, `transformation_phase=CI-1`.
- [ ] Open `/static/hub.html`; confirm release details load.
- [ ] Run the home demo once from beginning to end.
- [ ] Confirm text, identity, audio, image, and certificate steps complete.
- [ ] Open Analyst, NTOC, Governance, Developer, and Sectors pages.
- [ ] Confirm `/api/v1/country-pack`, `/api/v1/sectors`, and `/taxii2/` return data.
- [ ] Download the PowerPoint and open it offline.
- [ ] Record or copy a backup demo video to the laptop and USB drive.
- [ ] Close personal browser tabs and disable notifications.
- [ ] Connect the charger and test the projector resolution.
- [ ] Keep a mobile hotspot ready.
- [ ] Rehearse the full talk under three minutes.

### Local regression

```bash
cd mboashield
./.venv/bin/python -m pytest backend/tests -q
```

### Live smoke test

```bash
curl -fsS https://mboashield.onrender.com/health
curl -fsS https://mboashield.onrender.com/api/v1/program
curl -fsS https://mboashield.onrender.com/api/v1/country-pack
curl -fsS https://mboashield.onrender.com/taxii2/
```

---

## 13. Failure recovery during the presentation

| Failure | Immediate action |
|---|---|
| Render is sleeping | Open `/health`; speak the problem statement while it wakes |
| Home automation stops | Continue manually with Text and Identity panels |
| Audio/image upload fails | Show the completed Text result; move to Analyst/NTOC |
| Internet fails | Use local `./scripts/run_demo.sh` or the backup video |
| Empty dashboard | Create one check/incident first or explain the data flow |
| Authentication blocks an admin action | Return to public demo; explain national vs demo profiles |
| Unexpected score | Explain decision support and `certainty: none`; never argue that AI is infallible |

---

## 14. Other useful documents

| Document | Use |
|---|---|
| `docs/PRESENTER_GUIDE.md` | Short speaking script |
| `docs/COMPLETE_USER_GUIDE.md` | Detailed manual testing |
| `docs/E2E_WALKTHROUGH.md` | Longer technical tour |
| `docs/ARCHITECTURE.md` | System architecture |
| `docs/ACCESS_AND_CONFIG.md` | Roles, auth, configuration |
| `docs/manuals/` | Audit-oriented manuals |
| `docs/MBOASHIELD_2030_INDEX.md` | Transformation history |
| `docs/JURY_QA.md` | Jury questions and answers |

This master guide is the presenter's first reference. The other documents provide deeper supporting detail.
