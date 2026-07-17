# Security manual

**Version:** 1.9.0 � **Threat model:** [`../V1_0_THREAT_MODEL.md`](../V1_0_THREAT_MODEL.md)

## Control pillars

1. **Identity** � passwords, MFA, OIDC/SAML/LDAP, sessions, partner keys (Phase 6)
2. **Authorization** � RBAC + scopes; soft vs hard auth
3. **Evidence integrity** � hashes, custody, retention (Phase 9)
4. **Verified communications** � signed announcements + public verify (Phase 11)
5. **AI honesty** � certainty none; model cards; consent (Phases 12/14)
6. **Infrastructure** � metrics, workers, network allowlists (Phase 13)

## Hardening before government go-live

1. `AUTH_ENFORCE=true`, `MFA_ENFORCE=true`, `DEPLOYMENT_PROFILE=government`
2. Strong unique `JWT_SECRET`, vault/announcement signing keys
3. Postgres with backups; no SQLite for durable gov data
4. Narrow CORS and trusted hosts
5. `INTEL_EGRESS_ALLOWLIST` not `*`
6. `PASSWORD_RESET_RETURN_TOKEN=false`, `SAML_ALLOW_UNSIGNED=false`
7. Review `/health` `security_warnings`
8. Confirm risk register open items have owners

## Trust boundaries

- Public: `/`, `/static/*`, `/health`, `/verify/a/*`, citizen checks (demo)
- Privileged: analyst/admin APIs when auth enforced
- Machine: `X-API-Key` / OAuth2 client credentials with scopes

## AI-specific rules

- Do not claim forensic certainty in UI copy.
- Treat uploaded content and claim text as untrusted data.
- Model registry checksums must verify before enabling new weights.
- Analyst feedback affects calibration only as optional `calibrated_score`.

## Reporting

Security findings should reference threat-model IDs (`TM-*`) and risk register entries (`RISK-*`) via Governance APIs.
