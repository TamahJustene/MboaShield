# Disaster recovery runbook (MboaShield 2030 T6)

**Owner:** Platform / CERT ops  
**Related:** [`HA_AND_SCALE.md`](HA_AND_SCALE.md) � [`manuals/OPERATIONS.md`](manuals/OPERATIONS.md) � [`manuals/KMS_AND_SECRETS.md`](manuals/KMS_AND_SECRETS.md)

---

## 1. Targets (pilot)

| Objective | Target | Notes |
|---|---|---|
| **RPO** | <= 15 minutes | Managed Postgres PITR / continuous backup |
| **RTO** | <= 4 hours | Restore DB + redeploy API/workers + DNS |
| **Evidence vault** | Object storage versioning | Re-hydrate from bucket + DB metadata |

Demo SQLite has **no** multi-region RPO guarantee.

---

## 2. Backup inventory

| Asset | Backup method |
|---|---|
| Postgres | Automated snapshots + PITR |
| Object/vault files | Versioned bucket |
| Secrets | KMS / secret manager (not only disk) |
| Helm values | Git (no secrets) |

---

## 3. Restore procedure (Postgres)

1. Declare incident; freeze writes if possible.
2. Provision restore instance from PITR to target timestamp.
3. Point `DATABASE_URL` at restored instance (secret update).
4. `helm upgrade` / redeploy API with new secret; run `alembic upgrade head` if needed.
5. Verify `GET /health`, `GET /api/v1/program`, sample `POST /api/v1/trust/assess`.
6. Re-enable ingress / DNS.
7. Record drill log (section 5).

---

## 4. Announcement / signing keys

If signing keys are lost, rotate via KMS and re-issue announcements; historical signatures may fail verify until key history is restored. Prefer dual-key windows for future releases.

---

## 5. DR drill checklist

| Step | Done | Date / operator |
|---|---|---|
| Backup restore tested in non-prod | | |
| `/health` 200 after restore | | |
| Trust assess sample OK | | |
| NTOC / analyst UI loads | | |
| RPO/RTO measured vs target | | |
| Findings filed | | |

**Last drill:** _not yet recorded � schedule before national go-live._

---

## 6. Communication

Notify CERT / MINPOSTEL stakeholders of maintenance windows. Do not claim ISO/NIST DR certification without audit.
