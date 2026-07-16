# Phase 5 Plan - Hardened Identity

**Version target:** 0.9.0  
**Depends on:** Phase 4 (v0.8.0)  
**Status:** COMPLETE (v0.9.0)

## Why
Government and partner deployments need production identity controls beyond
demo JWT login: MFA, OIDC federation readiness, and scoped partner API keys.

## In scope
1. TOTP MFA setup / challenge / verify / disable
2. OIDC provider configuration and authorize/callback scaffolds
3. Partner API keys with hashed secrets and scopes
4. API-key authentication path alongside JWT
5. Password strength checks and production JWT secret warnings
6. Identity admin UI for MFA status and API key management

## Out of scope
- Live connection to a specific national IdP (config-ready only)
- Hardware WebAuthn keys
- Full SCIM provisioning
