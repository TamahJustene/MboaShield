# Changelog

All notable changes to MboaShield are documented here.

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
