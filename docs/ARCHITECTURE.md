# MboaShield Architecture

## Current state (v0.8.0 - Phase 4 analytics)

```text
National Trust Dashboard (frontend/static/national.html)
        |
        v
api/v1/analytics.py
        |
services/analytics.py
  threat trends
  deepfake trends
  institution attacks
  regional heat map
  incident timeline
  response time
  AI feedback feedback
  citizen participation
        |
SQLAlchemy models
  verification_checks
  incident_reports / incident_events
  analysis_feedback
  users / certificates
```

## Analytics honesty

AI accuracy uses analyst feedback labels when available.
Disposition ratios (resolved vs dismissed) are operational proxies only.

## Prior layers still active

- Phase 1: auth/RBAC/audit + SQLAlchemy/Postgres
- Phase 2: national incident workflow + operator consoles
- Phase 3: modular intelligence engines + trust fusion

## Next

Phase 5: OAuth2/OIDC, MFA readiness, partner API keys
