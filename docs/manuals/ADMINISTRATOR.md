# Administrator manual

**Version:** 1.9.0

## Roles

See [`../ACCESS_AND_CONFIG.md`](../ACCESS_AND_CONFIG.md). Summary:

| Role | Typical duties |
|---|---|
| `admin` | Users, partners, intel, vault retention, AI platform, governance |
| `institution_admin` | Institution branding, members, announcements |
| `analyst` | Incident review, evidence, intel read, AI read |
| `citizen` | Checks, own history, consent |

## Soft vs hard auth

| Env | Behaviour |
|---|---|
| `AUTH_ENFORCE=false` | Demo: no 401/403 on permission gates |
| `AUTH_ENFORCE=true` | Government: JWT / API key / OAuth required |

Also set `DEPLOYMENT_PROFILE=government` and `MFA_ENFORCE=true` for privileged roles.

## Day-one admin checklist

1. Strong `JWT_SECRET`
2. Postgres `DATABASE_URL` + `alembic upgrade head`
3. Create/promote admin user; enable MFA
4. `AUTH_ENFORCE=true`
5. Narrow `CORS_ORIGINS`
6. Configure IdP (OIDC/SAML) or LDAP if required
7. Issue partner keys with least privilege
8. Confirm `/health` shows expected feature flags

## Consoles

| Console | Path |
|---|---|
| National / analytics | `/static/national.html` |
| Investigation | `/static/investigation.html` |
| Intel | `/static/intel.html` |
| Institution portal | `/static/institution-portal.html` |
| Announcements | `/static/announcements.html` |
| AI lab | `/static/ai-lab.html` |
| Governance | `/static/governance.html` |

## Governance duties

- Keep risk register statuses current (`/api/v1/governance/risks`)
- Review model/dataset cards before enabling new adapters
- Monitor compliance snapshot (`/api/v1/governance/compliance`)
- Ensure certainty policy remains `none` unless a calibrated card says otherwise
