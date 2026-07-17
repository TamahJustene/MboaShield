# High availability and scale (MboaShield 2030 T6)

**Scope:** Patterns for national pilots. Not a certification claim.

---

## 1. Application (Helm)

Chart: `deploy/helm/mboashield`

| Setting | Multi-AZ guidance |
|---|---|
| `replicaCount` / HPA | >= 2 API pods across zones |
| Pod anti-affinity | Prefer `topology.kubernetes.io/zone` spread (add in overlay) |
| Workers | Separate deployment; scale independently |
| Ingress | Multi-AZ load balancer; TLS at edge |

Example overlay notes:

```yaml
replicaCount: 3
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 12
worker:
  replicaCount: 2
```

Schedule API and worker pods with zone-aware topology spread constraints in the cluster overlay (provider-specific).

---

## 2. PostgreSQL HA

| Pattern | Use |
|---|---|
| Managed Postgres (RDS / Cloud SQL / Azure Flexible) | Preferred for national |
| Primary + sync standby | RPO near zero for committed writes |
| PITR / continuous backup | Meet RPO <= 15 minutes |
| Connection string via secret | Never bake passwords into images |

SQLite is **demo only**. National profile requires `DATABASE_URL=postgresql+...`.

---

## 3. Redis / workers

- Redis: managed with persistence if used for Celery broker, or accept job loss on crash with sync fallback (`WORKERS_ENABLED=false`).
- Run workers in >= 2 replicas when critical jobs must not queue behind a single node.

---

## 4. Load proof

```bash
# Locust
locust -f scripts/load/locustfile.py --host http://127.0.0.1:8000 --headless -u 20 -r 5 -t 2m

# k6
k6 run -e BASE_URL=http://127.0.0.1:8000 scripts/load/trust_assess.js
```

Record p95 for `/api/v1/trust/assess` and attach to go-live evidence pack.

---

## 5. Resilience metadata API

`GET /api/v1/infra/resilience` � published targets and script paths.
