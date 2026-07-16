# Changelog

All notable changes to MboaShield are documented here.

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
