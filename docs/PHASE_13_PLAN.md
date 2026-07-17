# Phase 13 - Enterprise Infrastructure

**Version:** 1.7.0  
**Status:** COMPLETE  

## Delivered

- Prometheus `/metrics` + Grafana overview dashboard
- Celery task workers (intel ingest, vault retention, AI evaluation) with sync fallback
- Infra status and job enqueue APIs under `/api/v1/infra`
- `docker-compose.gov.yml` (Postgres + Redis + RabbitMQ + observability)
- Helm chart `deploy/helm/mboashield` with HPA

## Demo vs government

| Mode | Compose | Workers |
|---|---|---|
| Demo / Render | `docker-compose.yml` (unchanged) | Off (`WORKERS_ENABLED=false`) |
| Government | `docker-compose.gov.yml` | On (Celery + RabbitMQ/Redis) |

## Rollback

- Keep using `docker-compose.yml`
- Set `WORKERS_ENABLED=false` and `METRICS_ENABLED=false`
- Helm: `helm rollback mboashield`
