# KMS and secrets (MboaShield 2030 T5)

**Audience:** Platform operators / CERT  
**Goal:** No long-lived production secrets stored only in plaintext env files.

---

## 1. Secrets that must not live in git

| Secret | Env today (demo) | Production |
|---|---|---|
| JWT signing | `JWT_SECRET` | KMS / secret manager inject at boot |
| Webhook HMAC | `WEBHOOK_SIGNING_SECRET` | Same |
| Announcement signing | `ANNOUNCEMENT_SIGNING_KEY` | HSM/KMS preferred |
| Vault signing | `VAULT_SIGNING_KEY` | HSM/KMS preferred |
| DB password | inside `DATABASE_URL` | Managed Postgres + IAM/secret rotation |
| OIDC client secret | `OIDC_CLIENT_SECRET` | IdP + secret manager |

`.env` is for **local/demo only**. National profile: `deploy/profiles/national.env` with placeholders.

---

## 2. Recommended pattern

1. Store secrets in cloud KMS / HashiCorp Vault / AWS Secrets Manager / GCP Secret Manager.
2. At container start, inject as env vars (short-lived process env is OK; never commit values).
3. Rotate `JWT_SECRET` with dual-key window when possible (future enhancement).
4. Prefer managed Postgres TLS; never expose DB ports publicly.

---

## 3. Checklist before go-live

- [ ] `AUTH_ENFORCE=true`
- [ ] `DEPLOYMENT_PROFILE=national` (or `government`)
- [ ] Non-default `JWT_SECRET`
- [ ] `CORS_ORIGINS` locked to known hosts
- [ ] MFA required for analyst/admin roles
- [ ] RLS SQL reviewed for Postgres (`deploy/sql/rls_tenant.sql`)
- [ ] `/api/v1/auth/security-status` shows empty `warnings` and green zero-trust checklist

---

## 4. Break-glass

Document offline admin recovery separately. Do not embed break-glass passwords in this repo.
