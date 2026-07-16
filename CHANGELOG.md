# Changelog

All notable changes to MboaShield are documented here.

## [0.7.0] - 2026-07-16

### Phase 3 - Modular AI intelligence engines

#### Added
- Ten modular engines under `backend/app/services/engines/`:
  text, image, audio, video (scaffold), identity, document (scaffold),
  network, source, behavior, metadata
- Shared engine contract: confidence, evidence, reasoning, risk_level,
  threat_category, recommendations (never claims certainty)
- Trust fusion producing Explainable Trust Score
- Intelligence API:
  - `GET /api/v1/intelligence/engines`
  - `POST /api/v1/intelligence/analyze`
  - `POST /api/v1/intelligence/analyze/media`
- Case analyze now returns `engines`, `trust_score`, and intelligence summary
- Single-check responses include additive `intelligence` snapshot

#### Changed
- Trust engine version bumped to 0.7.0
- Home AI case panel shows Explainable Trust Score and active engines

#### Preserved
- Existing `/api/v1/check/*` and `ai_analysis` envelope shapes
- Detector services and Phase 1/2 platform features

## [0.6.0] - 2026-07-16

### Phase 2 - Government workflows
- National incident workflow, analyst/citizen/institution consoles, timelines

## [0.5.0] - 2026-07-16

### Phase 1 - Government platform foundation
- SQLAlchemy/Postgres path, JWT/RBAC/audit, Docker Compose, CI

## [0.4.0] - 2026-07-16

- NLP text path, media/audio adapters, unified AI envelope, incidents
