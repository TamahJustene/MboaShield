# Access control & configuration

**Version:** 1.4.0  
**Purpose:** Know who can do what, how enforcement works, and how to change it safely.

Related: [`PRODUCT_STATUS.md`](PRODUCT_STATUS.md) - [`ARCHITECTURE.md`](ARCHITECTURE.md) - [`DEPLOY.md`](DEPLOY.md) - [`PHASE_10_PLAN.md`](PHASE_10_PLAN.md)

---

## 1. Two operating modes

| Mode | Env | Behaviour |
|---|---|---|
| **Demo / public** (current live) | `AUTH_ENFORCE=false` | `require_permission()` returns optional actor or `None`. **No 401/403.** |
| **Government / locked** | `AUTH_ENFORCE=true` | Must present JWT Bearer, `X-API-Key`, or OAuth2 access token; then RBAC / scopes. |

Code: `backend/app/api/deps.py` ? `require_permission()`.

**Profiles:** `DEPLOYMENT_PROFILE=demo|government|national` (affects security warnings).

**National default:** copy `deploy/profiles/national.env` (`AUTH_ENFORCE=true`). See `docs/manuals/KMS_AND_SECRETS.md` and SCIM at `/scim/v2/Users`.

---

## 2. Roles and permissions

Defined in `backend/app/core/rbac.py`.

| Role | Intended user | Permissions |
|---|---|---|
| `citizen` | Public registrants | `checks:create`, `incidents:create`, `history:read_own`, `ambassadors:complete`, `institutions:read` |
| `analyst` | SOC / trust analysts | citizen set + `incidents:review`, `history:read_all`, `audit:read`, `intel:read`, `evidence:read`, `evidence:write` |
| `institution_admin` | Verified org operators | create checks/incidents + `incidents:review`, `history:read_all`, `institutions:read`, `institutions:manage`, `intel:read`, `evidence:read` |
| `admin` | Platform operators | all of the above + `users:manage`, `partners:manage`, `intel:manage`, `evidence:manage`, `system:admin` |
| `partner` | Machine clients | API-key or OAuth2 client-credentials actor with **scopes** |

### Permissions enforced on routes

| Permission | Endpoints |
|---|---|
| `incidents:review` | incident patch/transition, analyst queue/summary, analytics feedback |
| `institutions:manage` | institution write + institutions-admin overview |
| `audit:read` | `GET /api/v1/audit/logs` |
| `history:read_all` | analytics aggregates |
| `partners:manage` | partner API keys + OAuth client registration |
| `users:manage` | `/api/v1/admin/users` |
| `intel:read` / `intel:manage` | `/api/v1/intel/*` |
| `evidence:read` / `evidence:write` / `evidence:manage` | `/api/v1/evidence*` |
| `institutions:manage` | Registry write + `/api/v1/institution-portal/*` (membership-scoped when enforced) |

---

## 3. Creating and promoting users

### Register (always citizen)

`POST /api/v1/auth/register`

### Admin invite / create (Phase 6)

`POST /api/v1/admin/users` with `{display_name, email, role, password?}`  
Returns `temporary_password` when password omitted. Requires `users:manage` when enforced.

### Promote via API

`PATCH /api/v1/admin/users/{id}` `{ "role": "admin" }`

### Promote via SQL (break-glass)

```sql
UPDATE users SET role = 'admin' WHERE email = 'you@example.com';
```

---

## 4. Federation

| Method | Enable | Notes |
|---|---|---|
| OIDC | `OIDC_ENABLED` + issuer/client/secret | Full code exchange + user upsert |
| SAML | `SAML_ENABLED` + IdP cert (or `SAML_ALLOW_UNSIGNED` lab only) | Metadata + ACS |
| LDAP/AD | `LDAP_ENABLED` + server URI + bind template | Group?role via `LDAP_GROUP_ROLE_MAP` |

---

## 5. MFA & trusted devices

- Enroll: `/auth/mfa/setup` ? `/enable`  
- Login challenge when `mfa_enabled`  
- `MFA_ENFORCE=true` blocks privileged roles until MFA enrolled  
- Trust device on MFA verify or `POST /auth/devices/trust`  
- `TRUSTED_DEVICE_SKIP_MFA=true` skips challenge when `device_token` valid  

---

## 6. Sessions & password recovery

- List/revoke: `/auth/sessions`, `/auth/sessions/revoke`  
- Forgot: `/auth/password/forgot` (no email enumeration)  
- Reset: `/auth/password/reset`  
- For demos/tests only: `PASSWORD_RESET_RETURN_TOKEN=true` returns token in JSON  

---

## 7. Partner machine auth

| Method | Header / flow |
|---|---|
| API key | `X-API-Key: msb_...` |
| OAuth2 client credentials | Create `/oauth/clients` ? `POST /oauth/token` ? Bearer access token |

---

## 8. Environment knobs

See `.env.example` for the full list. Critical:

| Variable | Effect |
|---|---|
| `AUTH_ENFORCE` | Soft vs hard API gate |
| `DEPLOYMENT_PROFILE` | `demo` / `government` |
| `MFA_ENFORCE` | Require MFA enrollment for MFA_REQUIRED_ROLES |
| `OIDC_*` / `SAML_*` / `LDAP_*` | Federation |
| `PASSWORD_*` | Policy + reset behaviour |
| `DATABASE_URL` | Postgres for durable gov data |
| `INTEL_ENABLED` / `INTEL_EGRESS_ALLOWLIST` | Compliant intel platform |
| `VAULT_ENABLED` / `VAULT_STORAGE` / `VAULT_MAX_BYTES` | Evidence vault |
| `VAULT_RETENTION_DAYS` / `VAULT_SIGNING_KEY` | Retention + export HMAC |
| `INSTITUTION_PORTAL_ENABLED` | Institution admin portal |
| `VERIFIED_COMMS_ENABLED` / `ANNOUNCEMENT_SIGNING_KEY` | Signed announcements |
| `PUBLIC_BASE_URL` | Absolute verify URLs in QR payloads |
| `ADVANCED_AI_ENABLED` | Model registry, calibration, evaluation APIs |
| `AI_EVAL_LATENCY_BUDGET_MS` | Golden-set eval latency ceiling (ms) |
| `METRICS_ENABLED` | Expose Prometheus `/metrics` |
| `WORKERS_ENABLED` | Celery async jobs (else sync fallback) |
| `REDIS_URL` / `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Worker broker + results |
| `GOVERNANCE_ENABLED` | Consent, risk register, model cards, compliance |
| `COUNTRY_PACK` | Country deploy template id (default `cm`) |

---

## 9. Hardening checklist

1. Attach Postgres; `alembic upgrade head`  
2. Strong `JWT_SECRET`  
3. Create/promote admin; enable MFA  
4. `AUTH_ENFORCE=true`, `MFA_ENFORCE=true`, `DEPLOYMENT_PROFILE=government`  
5. Narrow `CORS_ORIGINS`  
6. Configure national IdP (OIDC or SAML)  
7. Issue partner keys / OAuth clients with least privilege  
8. Keep `PASSWORD_RESET_RETURN_TOKEN=false` and `SAML_ALLOW_UNSIGNED=false`  
