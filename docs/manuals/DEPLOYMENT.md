# Deployment manual

**Version:** 1.9.0 - **Detail:** [`../DEPLOY.md`](../DEPLOY.md)

## Options

| Target | How |
|---|---|
| Local demo | `./scripts/run_demo.sh` |
| Docker demo | `docker compose up --build` |
| Government stack | `docker compose -f docker-compose.gov.yml up --build` |
| Kubernetes | `helm upgrade --install mboashield deploy/helm/mboashield` |
| Public demo URL | Render Blueprint (`render.yaml`) |

## Required env (minimum)

| Variable | Notes |
|---|---|
| `JWT_SECRET` | Required in any non-toy deploy |
| `DATABASE_URL` | Postgres for gov |
| `AUTH_ENFORCE` | `true` for gov |
| `PUBLIC_BASE_URL` | Absolute verify URLs |

Full catalogue: [`../ACCESS_AND_CONFIG.md`](../ACCESS_AND_CONFIG.md) and `.env.example`.

## Migrations

```bash
export DATABASE_URL=postgresql+psycopg://...
alembic -c backend/alembic.ini upgrade head
```

App also runs `create_all` on boot for demo friction reduction; Alembic remains source of truth for production.

## Health verification

1. `GET /health` ? `"status":"ok"`, expected `version`
2. Open `/` and run guided demo
3. `GET /metrics` if metrics enabled
4. Gov: Prometheus scrapes `api:8000/metrics`

## Rollback

- Demo: keep using `docker-compose.yml` (unchanged by Phase 13)
- Feature flags: set phase flags false (`GOVERNANCE_ENABLED`, `WORKERS_ENABLED`, -)
- Helm: `helm rollback mboashield`
