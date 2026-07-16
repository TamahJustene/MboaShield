# Changelog

All notable changes to MboaShield are documented here.

## [0.8.0] - 2026-07-16

### Phase 4 - National analytics

#### Added
- National analytics aggregation service
- National Trust Dashboard UI (`/static/national.html`)
- Analytics APIs:
  - `GET /api/v1/analytics/national`
  - `GET /api/v1/analytics/threats`
  - `GET /api/v1/analytics/regions`
  - `GET /api/v1/analytics/incidents/timeline`
  - `GET /api/v1/analytics/performance`
  - `GET /api/v1/analytics/participation`
  - `POST /api/v1/analytics/feedback`
- Metrics: threat trends, deepfake trends, institution attack pressure,
  regional heat map, incident timeline, response time, AI accuracy labels,
  citizen participation
- `analysis_feedback` table + Alembic `0003_phase4`
- Region selector on incident report form

#### Changed
- Version bumped to 0.8.0

#### Preserved
- All prior detection, workflow, intelligence, and auth APIs

## [0.7.0] - 2026-07-16

### Phase 3 - Modular AI intelligence engines

## [0.6.0] - 2026-07-16

### Phase 2 - Government workflows

## [0.5.0] - 2026-07-16

### Phase 1 - Government platform foundation

## [0.4.0] - 2026-07-16

- NLP/media adapters, AI envelope, incidents
