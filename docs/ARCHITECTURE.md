# MboaShield Architecture

## Current state (v0.6.0 — Phase 2 workflows)

```text
Browser UI
  home / reports / history / institutions
  analyst console / citizen dashboard
        |
        v
FastAPI create_app()
  api/v1/auth.py
  api/v1/platform.py      detection + incidents + ambassadors
  api/v1/government.py    workflow, analyst, citizen, institution admin
        |
  core/  config, security, rbac, middleware, errors
  db/    SQLAlchemy models + session (SQLite/Postgres)
  repositories.py
  services/
    detectors + ai_analysis
    incident_workflow.py   national state machine
```

## National incident pipeline

```text
open -> ai_analysis -> analyst_review -> institution_review
    -> decision -> public_advisory -> resolved -> archived
```

Legacy `reviewing` maps to `analyst_review`. `dismissed` is a terminal reject path (archivable).

Every transition persists:
- updated `incident_reports` row
- `incident_events` timeline row
- `audit_logs` entry for sensitive actions

## Security

JWT/RBAC from Phase 1 remain in place. `AUTH_ENFORCE=false` keeps demo open; set `true` for government deployments.

## Next phases

- Phase 3: modular AI engines + trust score fusion
- Phase 4: national analytics dashboards
- Phase 5: OIDC/MFA and partner APIs
