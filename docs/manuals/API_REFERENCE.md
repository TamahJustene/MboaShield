# API reference (narrative)

**Version:** 1.9.0 � **Machine OpenAPI:** [`openapi.json`](openapi.json) � **Interactive:** `/docs`

Base path for product APIs: `/api/v1`.

## Conventions

- JSON errors often use `error.message` (and FastAPI `detail` for some handlers).
- Soft auth: when `AUTH_ENFORCE=false`, permission dependencies do not 401.
- Auth when enforced: `Authorization: Bearer <jwt>`, or `X-API-Key`, or OAuth2 client credentials token.

## Surface map

| Area | Prefix / routes | Notes |
|---|---|---|
| Platform checks | `/check/*`, institutions, incidents, ambassadors | Core demo |
| Auth / identity | `/auth/*`, `/admin/users`, OAuth | MFA, OIDC, SAML, LDAP |
| Partners | `/partners/*` | API keys |
| Intelligence | `/intelligence/*` | Multi-engine analyze |
| Analytics | `/analytics/*` | National aggregates + feedback |
| Government workflow | government / incident transitions | Human gates |
| NTOC / cases | `/cases/*`, ntoc routes | Threat ops |
| Intel | `/intel/*` | Compliant sources only |
| Evidence vault | `/evidence/*` | Hash, custody, retention |
| Institution portal | `/institution-portal/*` | Domains, `msi_` keys |
| Announcements | `/announcements/*` | Signed publish |
| Public verify | `GET /verify/a/{id}` | Outside `/api/v1` |
| AI platform | `/ai-platform/*` | Registry, eval, calibration |
| Infra | `/infra/*` | Status + job enqueue |
| Governance | `/governance/*` | Consent, risks, cards |

## Root endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Version, feature flags, identity readiness |
| GET | `/metrics` | Prometheus exposition |
| GET | `/` | Citizen UI |
| GET | `/docs` | Swagger UI |
| GET | `/openapi.json` | Live OpenAPI schema |

## Example: analyze intelligence

```http
POST /api/v1/intelligence/analyze
Content-Type: application/json

{"text":"URGENT send MoMo now","lang":"en"}
```

Expect `trust_score.certainty == "none"` and optional `calibrated_score`.

## Example: consent

```http
POST /api/v1/governance/consent
Content-Type: application/json

{"subject_key":"citizen-demo","feature":"analytics_share","granted":true}
```

## Regenerating this inventory

```bash
python scripts/export_openapi.py
```

See also `openapi.summary.md` for a flat path list.
