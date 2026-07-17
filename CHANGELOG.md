# Changelog

All notable changes to MboaShield are documented here.

## [2.7.0] - 2026-07-17

### MboaShield 2030 — Phase T7 (country packs & sectors)

#### Added
- ADR-0008: Country packs and sector modules
- Expanded CM + template country packs (legal, IdP, default sectors)
- `GET /api/v1/country-pack`, `GET /api/v1/sectors`
- Sector dashboard `/static/sectors.html`
- Governance ISO/NIST framework map: `GET /api/v1/governance/framework-map`
- Config: `SECTORS_ENABLED`
- Tests: `test_2030_t7.py`

#### Changed
- Product version 2.7.0; transformation phase **T7**
- MboaShield 2030 transformation plan phases T0-T7 complete

## [2.6.0] - 2026-07-17

### MboaShield 2030 — Phase T6 (resilience & scale proof)

#### Added
- ADR-0007: Resilience and scale proof
- Locust + k6 load scenarios under `scripts/load/`
- `docs/HA_AND_SCALE.md`, `docs/DR_RUNBOOK.md` (RPO/RTO + drill checklist)
- `GET /api/v1/infra/resilience`
- Tests: `test_2030_t6.py`

#### Changed
- Product version 2.6.0; transformation phase **T6**
- Helm chart image tag bumped; multi-AZ notes in values

## [2.5.0] - 2026-07-17

### MboaShield 2030 — Phase T5 (zero-trust & identity scale)

#### Added
- ADR-0006: Zero-trust national identity default
- `deploy/profiles/national.env` (`AUTH_ENFORCE=true` national default)
- Zero-trust checklist on `/api/v1/auth/security-status`
- SCIM 2.0 read-only: `/scim/v2/Users`, `/scim/v2/ServiceProviderConfig`
- Postgres RLS template: `deploy/sql/rls_tenant.sql`
- KMS guide: `docs/manuals/KMS_AND_SECRETS.md`
- Tests: `test_2030_t5.py`

#### Changed
- Product version 2.5.0; transformation phase **T5**
- Demo soft-auth default unchanged for public Render

## [2.4.0] - 2026-07-17

### MboaShield 2030 — Phase T4 (interoperability)

#### Added
- ADR-0005: Interoperability layer
- `/api/v1/interop/*` — webhooks (HMAC + retry), STIX bundle, CAP export, CSV reports
- Tables: `webhook_endpoints`, `webhook_deliveries` (Alembic `0017_t4_interop`)
- Config: `INTEROP_ENABLED`, `WEBHOOK_SIGNING_SECRET`, `WEBHOOK_MAX_RETRIES`
- Developer portal updated for live interop endpoints
- Tests: `test_2030_t4.py`

#### Changed
- Product version 2.4.0; transformation phase **T4**
- Incident status updates emit `incident.status_changed` webhook events

## [2.3.0] - 2026-07-17

### MboaShield 2030 — Phase T3 (portal platform)

#### Added
- ADR-0004: Shared portal shell
- `portal-shell.js` — auth awareness, nav, tenant, FR/EN toggle
- Developer portal: `/static/developer.html`
- Shell migration: Analyst, NTOC, Institution portal
- Tests: `test_2030_t3.py`

#### Changed
- Product version 2.3.0; transformation phase **T3**

## [2.2.0] - 2026-07-17

### MboaShield 2030 — Phase T2 (National Digital Trust Network)

#### Added
- ADR-0003: Trust Network model
- `trust_relationships`, `exchange_channels`, `shared_alerts` (Alembic `0016_t2_trust_network`)
- APIs: `/api/v1/trust-network/relationships`, `/exchange/channels`, `/exchange/alerts`, `/status`
- Institution portal: trusted partners + share alert UI
- Tests: `test_2030_t2.py`

#### Changed
- Product version 2.2.0; transformation phase **T2**

## [2.1.0] - 2026-07-17

### MboaShield 2030 — Phase T1 (national trust object model)

#### Added
- ADR-0002: unified `TrustAssessment` resource
- `POST /api/v1/trust/assess`, `POST /api/v1/trust/assess/media`, `GET /api/v1/trust/assessments/{id}`
- `trust_assessments` table (Alembic `0015_t1_trust`)
- Home and citizen UI: national trust panel (legacy risk fields preserved)
- Tests: `test_2030_t1.py`

#### Changed
- Product version 2.1.0; transformation phase **T1**
- Home verifications call the trust API; `/api/v1/check/*` unchanged for partners

## [2.0.0] - 2026-07-17

### MboaShield 2030 — Phase T0 (architecture alignment)

#### Added
- National platform OpenAPI taxonomy (`pillar-*` tags)
- `GET /api/v1/program` — 2030 program metadata and pillar catalog
- `COUNTRY_PACK` configuration and `deploy/country-packs/cm/`
- Health fields: `program`, `transformation_phase`, `country_pack`
- Docs: 2030 vision, transformation plan, pillar registry, ADR-0001
- Tests: `test_2030_t0.py`

#### Changed
- Product version 2.0.0; Trust API title and OpenAPI description
- No breaking changes to `/api/v1` paths or request bodies

## [1.9.0] - 2026-07-16

### Phase 15 - Documentation Suite

#### Added
- Role manuals under `docs/manuals/` (User, Administrator, Developer, Operations, Security, Deployment, Maintenance)
- Narrative API reference, Architecture guide, and AI Governance guide
- OpenAPI export script: `scripts/export_openapi.py` ? `docs/manuals/openapi.json` + summary
- Links from product README and PRODUCT_STATUS

#### Changed
- Product version bumped to 1.9.0
- Enterprise program Phases 6-15 marked complete

## [1.8.0] - 2026-07-16

### Phase 14 - Governance

#### Added
- Consent records for optional citizen features (`analytics_share`, `feedback_learning`, `partner_notify`)
- Risk register linked to threat-model refs (`TM-*`)
- Model cards and dataset cards for AI transparency
- Responsible-AI / privacy / compliance control catalogue
- Compliance dashboard aggregating risks, controls, and recent audit
- APIs: `/api/v1/governance/*`
- Admin UI: `/static/governance.html`
- Alembic migration `0014_phase14`
- Feature flag: `GOVERNANCE_ENABLED`

#### Changed
- Product version bumped to 1.8.0

## [1.7.0] - 2026-07-16

### Phase 13 - Enterprise Infrastructure

#### Added
- Prometheus metrics at `GET /metrics` with request and worker counters
- Celery workers for intel ingest, vault retention, and AI evaluation (sync fallback when `WORKERS_ENABLED=false`)
- Infra APIs: `/api/v1/infra/status` and `/api/v1/infra/jobs/*`
- `docker-compose.gov.yml` with Postgres, Redis, RabbitMQ, worker, beat, Prometheus, Grafana, Loki
- Helm chart `deploy/helm/mboashield` with HPA and worker deployment
- Grafana dashboard as code under `deploy/grafana/`
- Feature flags: `METRICS_ENABLED`, `WORKERS_ENABLED`, `REDIS_URL`, `CELERY_*`

#### Changed
- Product version bumped to 1.7.0
- Demo `docker-compose.yml` unchanged (rollback-friendly)

## [1.6.0] - 2026-07-16

### Phase 12 - Advanced AI Platform

#### Added
- Model registry with SHA-256 checksum verification for built-in adapters
- Runtime adapter layer (heuristic default, ONNX scaffold with fallback)
- Feedback-driven calibration summary and optional `calibrated_score` on trust fusion
- Golden-set evaluation harness (EN/FR) with latency budget checks
- APIs: `/api/v1/ai-platform/*`
- AI lab UI: `/static/ai-lab.html`
- Alembic migration `0012_phase12`
- Feature flag: `ADVANCED_AI_ENABLED`

#### Changed
- Trust engine package version bumped to 1.2.0
- Product version bumped to 1.6.0

## [1.5.0] - 2026-07-16

### Phase 11 - Verified Government Communications

#### Added
- Digitally signed government announcements with version history
- Public permanent verification at `/verify/a/{announcement_id}`
- QR verify payload and JSON/markdown authenticity certificates
- Publisher and public verify UIs
- Alembic migration `0010_phase11`
- Feature flag: `VERIFIED_COMMS_ENABLED`

#### Changed
- Product version bumped to 1.5.0

## [1.4.0] - 2026-07-16

### Phase 10 - Institution Administration Platform

#### Added
- Institution portal APIs: domains, memberships, branding, official accounts, scoped API keys, investigations, analytics
- Domain verification workflow (DNS TXT / token confirm / HTTP file)
- Institution API keys with `msi_` prefix (partner keys remain `msb_`)
- Portal UI: `/static/institution-portal.html`
- Alembic migration `0009_phase10`
- Feature flag: `INSTITUTION_PORTAL_ENABLED`

#### Changed
- Product version bumped to 1.4.0
- Institution model gains `branding_json` and `contact_email`

#### Preserved
- Existing registry CRUD, partner keys, NTOC, intel, vault, and detection APIs

## [1.3.0] - 2026-07-16

### Phase 9 - Digital Evidence Vault

#### Added
- Evidence vault with SHA-256 hashing, local FS storage (S3 adapter optional)
- Append-only custody chain with linked event hashes
- Custody transfer, signed JSON export packages, export verification
- Retention dry-run and purge worker endpoint
- Investigation workspace vault upload + listing
- Alembic migration `0008_phase9`
- Feature flag: `VAULT_ENABLED` (+ `VAULT_STORAGE`, size/retention/signing knobs)

#### Changed
- Product version bumped to 1.3.0
- Case evidence view includes vault items alongside linked verification checks

#### Preserved
- Existing `/api/v1/*` detection, NTOC, intel, identity, and analytics APIs

## [1.2.0] - 2026-07-16

### Phase 8 - Threat Intelligence Platform (compliant sources)

#### Added
- Intel source registry with ToS/license compliance metadata
- Connectors: RSS/Atom, official HTTP API, open data, partner webhook
- Hard reject of scrape / ToS-bypass source classes
- Egress allowlist (`INTEL_EGRESS_ALLOWLIST`) and ingest quotas
- Correlation engine (shared URLs/handles) + campaign clustering
- National threat intelligence report (JSON + markdown)
- Alembic migration `0007_phase8`
- Ops UI: `/static/intel.html`
- Feature flag: `INTEL_ENABLED`

#### Changed
- Product version bumped to 1.2.0

#### Preserved
- Existing `/api/v1/*` detection, NTOC, identity, and analytics APIs

## [1.1.0] - 2026-07-16

### Phase 7 - National Trust Operations Center

#### Added
- NTOC dashboard, threat level, regional map, institution health
- Investigation cases with notes, assignments, search, workspace
- Read-only linked evidence viewer for cases
- In-app notifications (+ optional webhook) on incident transitions and case assignment
- Alembic migration `0006_phase7`
- UIs: `/static/ntoc.html`, `/static/investigation.html`

#### Changed
- Product version bumped to 1.1.0

#### Preserved
- Existing analyst queue, national analytics, identity, detection APIs

## [1.0.0] - 2026-07-16

### Phase 6 - Enterprise Identity Platform

#### Added
- Working OIDC authorization-code exchange with federated user upsert
- SAML 2.0 SP metadata + ACS (certificate verification; lab unsigned flag)
- LDAP / Active Directory bind login with group-to-role mapping
- OAuth2 client-credentials clients and `/api/v1/oauth/token`
- Server-side auth sessions with revoke and revoke-all
- Trusted devices with optional MFA skip
- Password policy knobs + forgot/reset token flow
- Administrative user management API (`/api/v1/admin/users`)
- Auth events table + deployment profile / tenant bootstrap
- Alembic migration `0005_phase6`
- Expanded identity console UI
- Feature flags: `OIDC_ENABLED`, `SAML_ENABLED`, `LDAP_ENABLED`, `MFA_ENFORCE`

#### Changed
- Product version bumped to 1.0.0
- Login/register/MFA flows now create tracked sessions
- Security status reports federation readiness and deployment profile

#### Preserved
- Local JWT register/login/refresh/logout
- Soft demo mode (`AUTH_ENFORCE=false`)
- Partner API keys (`X-API-Key`)
- All detection, workflow, intelligence, and analytics APIs

## [0.9.0] - 2026-07-16

### Phase 5 - Hardened identity

#### Added
- TOTP MFA setup, enable, verify challenge, and disable
- OIDC provider listing + authorize/callback scaffolds
- Partner API keys (`msb_...`) with hashed storage and scopes
- API-key authentication via `X-API-Key` alongside JWT
- Auth security status endpoint and production secret warnings
- Password strength validation on register
- Identity UI (`/static/identity.html`)
- Alembic migration `0004_phase5`

#### Changed
- Login returns AuthSessionOut (supports MFA challenge)
- Version bumped to 0.9.0

#### Preserved
- Existing JWT register/refresh/logout flows
- Demo soft mode (`AUTH_ENFORCE=false`)
- All prior detection, workflow, intelligence, and analytics APIs

## [0.8.0] - 2026-07-16
### Phase 4 - National analytics

## [0.7.0] - 2026-07-16
### Phase 3 - Modular AI intelligence engines

## [0.6.0] - 2026-07-16
### Phase 2 - Government workflows

## [0.5.0] - 2026-07-16
### Phase 1 - Government platform foundation
