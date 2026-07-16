# Changelog

All notable changes to MboaShield are documented here.

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
