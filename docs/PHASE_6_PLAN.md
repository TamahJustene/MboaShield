# Phase 6 - Enterprise Identity Platform

**Version:** 1.0.0  
**Status:** COMPLETE  
**Date:** 16 July 2026  

## Objectives delivered

- OIDC authorization code exchange + federated user upsert  
- OAuth2 client credentials (`/api/v1/oauth/token`, `/oauth/clients`)  
- SAML 2.0 SP metadata + ACS (signed via IdP cert, or `SAML_ALLOW_UNSIGNED` for lab)  
- LDAP/AD bind login with group?role map  
- Server-side auth sessions + revoke / revoke-all  
- Trusted devices + optional MFA skip  
- Password policy + forgot/reset tokens  
- Admin user management API (`/api/v1/admin/users`)  
- Expanded auth events + audit  
- Deployment profile / tenant bootstrap (`DEPLOYMENT_PROFILE`, `TENANT_ID`)  

## Key surfaces

| Surface | Path |
|---|---|
| Identity UI | `/static/identity.html` |
| Security status | `GET /api/v1/auth/security-status` |
| OIDC | `/api/v1/auth/oidc/*` |
| SAML | `/api/v1/auth/saml/metadata`, `/saml/acs` |
| LDAP | `POST /api/v1/auth/ldap/login` |
| Sessions | `/api/v1/auth/sessions` |
| Devices | `/api/v1/auth/devices` |
| Password | `/api/v1/auth/password/forgot`, `/reset` |
| Admin users | `/api/v1/admin/users` |
| OAuth clients | `/api/v1/oauth/clients`, `/oauth/token` |

## Tests

`pytest backend/tests` - 55 passed at Phase 6 close.

## Rollback

Disable features via `OIDC_ENABLED`, `SAML_ENABLED`, `LDAP_ENABLED`. Local password login remains.
