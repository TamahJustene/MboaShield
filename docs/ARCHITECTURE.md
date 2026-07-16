# MboaShield Architecture

## Current state (v0.9.0 - Phase 5 identity)

```text
Identity UI / Partner systems
        |
        +-- JWT bearer
        +-- MFA challenge (TOTP)
        +-- X-API-Key (partner scopes)
        +-- OIDC authorize/callback scaffolds
        v
api/v1/auth.py
api/v1/partners.py
core/security.py
partner_api_keys + users.mfa_* tables
```

## Identity controls

- Password login with lockout + strength checks
- Optional TOTP MFA with challenge token
- OIDC provider configuration via env
- Partner API keys hashed at rest, scoped permissions
- Production warnings for weak JWT/CORS/AUTH_ENFORCE settings

## Prior layers

- Phase 1 chassis, Phase 2 workflows, Phase 3 engines, Phase 4 analytics

## Next hardening opportunities

- Complete OIDC code exchange against a live IdP
- WebAuthn / hardware keys
- Evidence vault and partner webhook delivery
