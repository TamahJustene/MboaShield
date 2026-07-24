# MboaShield v1.0 - Implementation Roadmap (Phases 6-15)

**Status:** APPROVED FOR PLANNING - application code gated  
**Baseline:** v0.9.0 - **Index:** [`V1_0_ENTERPRISE_INDEX.md`](V1_0_ENTERPRISE_INDEX.md)  
**Rules:** One phase at a time - no breaking `/api/v1` - no mocks/TODOs - tests + docs every phase - compliant intel only  

**Quality gate (every phase):** all pytest green - static checks - security review of touched auth surfaces - docs updated - backward compatibility verified - demo profile still boots with `./scripts/run_demo.sh`

---

## Cross-cutting constraints

| Constraint | Enforcement |
|---|---|
| Never rebuild | Extend routers/services/tables |
| Multi-country | Tenant/deployment profile config; no forks |
| Soft auth demo | `AUTH_ENFORCE=false` remains valid demo profile |
| Honest AI | Keep `certainty: "none"` unless calibrated fields added separately |
| Phase 8 sources | Official APIs / RSS / authorized feeds only |

---

## Phase 6 - Enterprise Identity Platform

**Planned version:** 1.0.0  
**Estimated complexity:** Very High  

### Objectives

Complete production identity: OIDC/OAuth2 callback, SAML 2.0, LDAP/AD, SSO session management, trusted devices, password policies/recovery, administrative user management, device management, expanded audit logging - without removing local JWT/MFA/partner keys.

### Deliverables

- Working OIDC authorization code exchange + user upsert  
- OAuth2 client credentials for partners (optional alongside API keys)  
- SAML 2.0 SP (ACS, metadata)  
- LDAP/Active Directory bind + group?role mapping allowlist  
- Server-side session registry + revoke / revoke-all  
- Trusted devices + step-up MFA  
- Configurable password policy + recovery tokens  
- Admin User Management API + UI (roles, disable, invite)  
- Device management UI section  
- Audit events for all identity mutations  
- Deployment profile: `demo` vs `government`  

### Dependencies

- Existing `auth.py`, `security.py`, `rbac.py`, MFA, OIDC env scaffold  
- Postgres recommended for gov profile  

### Affected files (expected)

- `backend/app/api/v1/auth.py`, new `users_admin.py`  
- `backend/app/core/security.py`, `config.py`, `rbac.py`  
- `backend/app/db/models.py`, repositories (identity split)  
- `frontend/static/identity.html` (+ admin users section)  
- `.env.example`, `render.yaml`, `docs/ACCESS_AND_CONFIG.md`  

### Database changes

- `sessions`, `trusted_devices`, `password_reset_tokens`, `auth_events`  
- User fields: lock policy counters already present - extend as needed  
- `tenants` / `deployment_profiles` (minimal)  
- Alembic `0005_phase6_identity`  

### API changes (additive)

- Complete `POST/GET` OIDC callback (replace stub)  
- `/auth/saml/metadata`, `/auth/saml/acs`  
- `/auth/ldap/login` (or unified login `provider=ldap`)  
- `/auth/sessions`, `/auth/sessions/revoke`  
- `/auth/password/forgot`, `/auth/password/reset`  
- `/admin/users` CRUD (requires `users:manage`)  
- Optional `/oauth/token` client_credentials  

### Frontend changes

- Identity console: SSO buttons, sessions, devices, user admin  
- No change to guided citizen home beyond optional login link  

### Testing plan

- Unit: token exchange parsers, password policy, role mapping  
- API: register/login/MFA regression; OIDC against mock IdP; SAML fixture; LDAP testcontainer or mocked bind  
- Enforce-mode matrix: soft vs hard  
- Regression: partner keys, refresh, logout  

### Rollback plan

- Feature flags: `OIDC_ENABLED`, `SAML_ENABLED`, `LDAP_ENABLED`  
- Alembic downgrade `0005`  
- Keep prior JWT login path always available  

### Documentation updates

- ACCESS_AND_CONFIG, ARCHITECTURE, DEPLOY, CHANGELOG, PRODUCT_STATUS  
- Phase 6 plan completion note  

### Risk assessment

| Risk | Mitigation |
|---|---|
| Breaking AuthSessionOut | Additive fields only |
| IdP misconfig lockout | Local admin emergency break-glass documented |
| LDAP credential exposure | Never log binds; TLS required |

---

## Phase 7 - National Trust Operations Center

**Planned version:** 1.1.0 - **Complexity:** Very High - **Depends on:** Phase 6 (auth for analysts)

### Objectives

Live threat dashboard, national threat level, regional map, investigation workspace, case assignment/notes/search, evidence viewer (read path), timeline, notifications, institution health - extending analyst/national UIs.

### Deliverables

- NTOC home UI  
- Threat level service (config thresholds)  
- Cases API + assignment + notes + search  
- Notifications (in-app + webhook/email hooks)  
- Institution health scores from incidents/SLA  
- Investigation workspace linking incident + checks + timeline  

### Dependencies

- Phase 6 sessions/RBAC  
- Existing analytics + incident workflow  

### Affected files

- New `api/v1/cases.py`, `services/ntoc.py`, `services/notifications.py`  
- `frontend/static/national.html`, `analyst.html`, new `ntoc.html` / `investigation.html`  
- models + Alembic `0006_phase7_ntoc`  

### Database changes

- `cases`, `case_notes`, `case_assignments`, `notifications`, `institution_health_snapshots`  

### API changes

- `/api/v1/ntoc/threat-level`, `/ntoc/dashboard`  
- `/api/v1/cases` CRUD-ish + assign + notes + search  
- `/api/v1/notifications`  
- Preserve `/analyst/*`  

### Frontend changes

- NTOC dashboard; investigation workspace; notification bell  

### Testing plan

- Workflow+case linkage; RBAC; search pagination; notification creation on transition  

### Rollback plan

- Flag `NTOC_ENABLED`; unused tables harmless  

### Documentation updates

- ARCHITECTURE journeys; PRODUCT_STATUS; operator quickstart stub  

### Risks

- Scope creep into vault ? evidence **viewer** only; write vault is Phase 9  
- Map tiles: use config GIS or offline SVG regions first (no unpaid scrape)

---

## Phase 8 - Threat Intelligence Platform (compliant sources)

**Planned version:** 1.2.0 - **Complexity:** High - **Depends on:** Phase 7 optional; Phase 6 required for admin of sources

### Objectives

Ingest intelligence from **authorized** sources only; correlate to incidents; detect coordinated campaigns; generate national intel reports.

### Allowed source classes

- Government websites / open data portals (official HTTP APIs or published RSS)  
- News RSS/Atom feeds with license-compliant use  
- Official platform APIs (Meta Graph, X API, YouTube Data API, Telegram Bot/public API where ToS permits) with stored credentials  
- Partner push webhooks  
- **Forbidden:** ToS-violating scraping, bypassing auth/paywalls, credential stuffing  

### Deliverables

- Source registry + connector interface  
- Ingest workers (can run sync in-process until Phase 13)  
- Correlation engine (URLs, handles, text similarity hashes)  
- Campaign clustering  
- National intelligence report export (PDF/JSON)  

### Affected files

- `services/intel/`, `api/v1/intel.py`, connectors per source class  
- Alembic `0007_phase8_intel`  
- Admin UI for sources  

### Database changes

- `intel_sources`, `intel_items`, `intel_campaigns`, `intel_correlations`  

### API changes

- `/api/v1/intel/sources`, `/intel/items`, `/intel/campaigns`, `/intel/reports`  

### Testing plan

- Connector contract tests with recorded fixtures (VCR)  
- Correlation unit tests  
- Compliance metadata required on every source  

### Rollback plan

- Disable schedulers; keep data  

### Documentation updates

- Intel connector ToS register; THREAT_MODEL -17 affirmation  

### Risks

- Legal: connector review checklist mandatory before enable  
- Volume: backpressure + quotas  

---

## Phase 9 - Digital Evidence Vault

**Planned version:** 1.3.0 - **Complexity:** Very High - **Depends on:** Phase 7 cases

### Objectives

Evidence IDs, hashing, chain of custody, digital signatures, search, export, retention, audit trail.

### Deliverables

- Vault service + object storage adapter (local FS adapter for demo; S3 for gov)  
- Custody API  
- Signed export packages  
- Retention worker  

### Affected files

- `services/vault/`, `api/v1/evidence.py`  
- Alembic `0008_phase9_vault`  

### Database changes

- `evidence_items`, `evidence_custody_events`, `evidence_exports`, retention fields  

### API changes

- `/api/v1/evidence` register/list/get/transfer/export/search  

### Frontend changes

- Evidence viewer write path in investigation workspace  

### Testing plan

- Hash stability; custody append-only; export signature verify; retention dry-run  

### Rollback plan

- Flag `VAULT_ENABLED`; FS adapter default for demo  

### Risks

- Large files ? size caps; async when Phase 13 ready  

---

## Phase 10 - Institution Administration Platform

**Planned version:** 1.4.0 - **Complexity:** High - **Depends on:** Phase 6

### Objectives

Institution users, domains, official accounts, branding, API keys, investigations view, analytics.

### Deliverables

- Institution admin portal expansions  
- Domain verification workflow  
- Scoped API keys per institution  
- Branding config  

### DB / API

- `institution_domains`, `institution_memberships`, branding JSON  
- `/api/v1/institution-portal/*`  

### Testing / rollback / docs

- Standard gate; feature flag `INSTITUTION_PORTAL_ENABLED`  

---

## Phase 11 - Verified Government Communications

**Planned version:** 1.5.0 - **Complexity:** High - **Depends on:** Phase 10 + Phase 9 (optional sign keys in vault/KMS)

### Objectives

Digitally signed announcements, QR verification, permanent verify URL, version history, authenticity certificate, public verification page.

### Deliverables

- Announcement lifecycle API + public `/verify/a/{id}`  
- QR payload  
- Version history  
- Certificate PDF/JSON  

### Risks

- Key management - use KMS/env keys; rotate with versioned kid  

---

## Phase 12 - Advanced AI Platform

**Planned version:** 1.6.0 - **Complexity:** Very High - **Depends on:** Engines package

### Objectives

ONNX Runtime, transformers, ViT, Whisper, sentence-transformers, model registry, monitoring, confidence calibration, continuous evaluation, human feedback learning, XAI - **without** claiming certainty by default.

### Deliverables

- Model registry + checksums  
- Runtime adapters behind existing engine interfaces  
- Evaluation harness + feedback loop from analytics labels  
- Calibrated_score optional field (parallel to trust)  

### Rules

- Video/document engines upgrade in place (remove scaffold only when real)  
- Keep heuristic path as fallback  

### Testing

- Golden sets EN/FR; latency budgets; no certainty regressions  

---

## Phase 13 - Enterprise Infrastructure

**Planned version:** 1.7.0 - **Complexity:** Very High  

### Objectives

PostgreSQL default for gov, Redis, RabbitMQ, Celery, object storage, Prometheus, Grafana, Loki, horizontal scaling, container optimization, Kubernetes, Helm.

### Deliverables

- `deploy/helm/mboashield`  
- `docker-compose.gov.yml`  
- Workers for intel/vault/retention/AI  
- Metrics endpoints + dashboards as code  
- HPA policies  

### Rollback

- Demo compose unchanged; Helm rollback  

### Risks

- Over-infra before traffic - keep compose.gov as intermediate  

---

## Phase 14 - Governance

**Planned version:** 1.8.0 - **Complexity:** Medium-High  

### Objectives

Responsible AI controls, privacy/consent, risk register, model cards, dataset cards, compliance + audit dashboards.

### Deliverables

- Governance APIs + admin UI  
- Consent records for citizen optional features  
- Risk register linked to threat model IDs  

---

## Phase 15 - Documentation Suite

**Planned version:** 1.9.0 - **Complexity:** Medium  

### Objectives

Administrator, Developer, User, Operations, Security, Deployment, Maintenance manuals; API reference (beyond OpenAPI); Architecture guide; AI Governance guide.

### Deliverables

- `docs/manuals/*` generated from living source docs + OpenAPI export  
- Link from README and PRODUCT_STATUS  

**Note:** Phases 6-14 already update docs; Phase 15 consolidates and polishes for external audit.

---

## Testing strategy (program-level)

| Layer | When |
|---|---|
| Unit | Every phase |
| Integration / API | Every phase |
| UI smoke (manual + optional Playwright later) | Phases 7, 10, 11 |
| Performance / load | Phase 13 (+ spot checks on AI Phase 12) |
| Security tests | Phase 6 exit + before gov go-live |
| Accessibility | Phases 7, 10, 15 |
| Regression | Full pytest each phase |
| AI evaluation | Phase 12+ |

---

## Suggested sequencing calendar (indicative, not rush)

| Phase | Relative effort |
|---|---|
| 6 Identity | 1.0 unit |
| 7 NTOC | 1.0 |
| 8 Intel | 0.8 |
| 9 Vault | 0.9 |
| 10 Institution | 0.7 |
| 11 Verified comms | 0.6 |
| 12 Advanced AI | 1.2 |
| 13 Infra | 1.0 |
| 14 Governance | 0.5 |
| 15 Docs | 0.4 |

Optimize for correctness over calendar speed. Competition demo remains on v0.9 demo profile until Phase 6+ deliberately versioned.

---

## Exit criteria to start coding Phase 6

- [x] Architecture review published  
- [x] System design published  
- [x] Threat model published  
- [x] This roadmap published  
- [ ] Stakeholder acknowledgment to begin Phase 6 only  

**Upon acknowledgment:** implement Phase 6 exclusively per this work order; commit; update CHANGELOG to 1.0.0; do not start Phase 7 until Phase 6 quality gate passes.
