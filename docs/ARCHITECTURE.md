# Architecture (MVP)

```
Browser UI (frontend/)
        |
        v
FastAPI (backend/app/main.py)
        |
        +-- services/text_check.py      -> rumour / claim risk
        +-- services/impersonation.py   -> institutional registry match
        +-- services/media_check.py     -> image heuristics (ML-ready)
        +-- services/ambassadors.py     -> lessons + certificate

Static data (data/*.json)
Demo samples (frontend/static/samples/)
```

## Design choices
- **Monolith MVP**: one process, zero infra drama on stage.
- **Service plug points**: replace heuristics with models without changing routes.
- **No DB yet**: JSON files; enough for demo; SQLite later.
