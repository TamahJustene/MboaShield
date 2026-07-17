# Operations manual

**Version:** 1.9.0

## Health and signals

| Check | Endpoint / tool |
|---|---|
| Liveness | `GET /health` |
| Metrics | `GET /metrics` (Prometheus) |
| Infra status | `GET /api/v1/infra/status` |
| NTOC threat level | NTOC APIs / national UI |

## Demo vs government

| Mode | Compose | Workers | Auth |
|---|---|---|---|
| Demo / Render | `docker-compose.yml` | Off | Soft |
| Government | `docker-compose.gov.yml` | Celery + Redis/RabbitMQ | Hard |

## Common operator tasks

### Re-run vault retention (dry run)

```http
POST /api/v1/infra/jobs/vault-retention?dry_run=true
```

### Trigger intel ingest (sync or async)

```http
POST /api/v1/infra/jobs/intel-ingest/{source_id}
```

### Run golden AI evaluation

```http
POST /api/v1/ai-platform/evaluation/run
{"dataset":"en"}
```

## Observability (gov compose)

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (admin / `mboashield`)
- Loki: `http://localhost:3100`
- Dashboard as code: `deploy/grafana/dashboards/`

## Incident workflow states

`open` ? `ai_analysis` ? `analyst_review` ? `institution_review` ? `decision` ? `public_advisory` ? `resolved` ? `archived`

Never auto-publish advisories from AI alone.

## On-call notes

- Free Render sleeps after idle; wake `/health` before demos.
- SQLite is fine for demo; government requires Postgres.
- Prefer sync job mode if Redis/RabbitMQ is down (`WORKERS_ENABLED=false`).
