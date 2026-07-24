# Architecture guide

**Version:** 1.9.0 - **Living doc:** [`../ARCHITECTURE.md`](../ARCHITECTURE.md)

## One-line view

Browser / IdP / partners ? FastAPI chassis ? services/stores/engines ? SQLAlchemy (SQLite or Postgres) + optional object storage and Celery workers.

## Layering (Phases 6-14)

| Layer | Responsibility |
|---|---|
| Chassis | Config, JWT, RBAC, middleware, DB session |
| Platform | Checks, users, institutions, audit |
| Government | Incident workflow consoles |
| Intelligence | Engines + trust fusion |
| Analytics | National aggregates |
| Identity | MFA, federation, partners |
| NTOC | Cases, threat level |
| Intel | Compliant ingest |
| Vault | Evidence custody |
| Institution portal | Org admin + keys |
| Verified comms | Signed announcements |
| Advanced AI | Registry, calibration, eval |
| Infrastructure | Metrics, workers, Helm |
| Governance | Consent, risks, cards |

## Data stores

- Primary: SQLite (demo) or PostgreSQL (gov)
- Vault objects: local FS or S3
- Optional: Redis / RabbitMQ for Celery

## Trust engine policy

- Engine package version tracked separately from product version
- Heuristic fallback always available
- `certainty` default `"none"`
- Optional `calibrated_score` from feedback (Phase 12)

## Deployment topologies

1. Single container (Render / demo compose)
2. Gov compose: api + worker + beat + observability
3. Kubernetes via Helm with HPA

## Further reading

- System design: [`../V1_0_SYSTEM_DESIGN.md`](../V1_0_SYSTEM_DESIGN.md)
- Architecture review: [`../V1_0_ARCHITECTURE_REVIEW.md`](../V1_0_ARCHITECTURE_REVIEW.md)
- Data model notes: [`../DATA_MODEL_V1.md`](../DATA_MODEL_V1.md)
