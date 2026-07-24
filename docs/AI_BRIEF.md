# AI Brief — MboaShield

Pass this file to any AI agent working on the repository.

## Identity

- **Product:** MboaShield — sovereign digital trust platform for Cameroon against deepfakes, disinformation, digital identity theft, plus digital-literacy education.
- **Solo founder:** Justene Nkwagoh Tamah (`tamahjustene45@gmail.com`), GitHub `TamahJustene`.
- **Repo:** https://github.com/TamahJustene/MboaShield
- **Live demo:** https://mboashield.onrender.com
- **Current release:** v2.8.0 (2030 T0–T7 + CI-1)
- **Active focus:** Product readiness — hard auth coverage, tenancy, secrets, E2E, bilingual UX, measured resilience.

## Non-negotiables

1. Solo founder product — do not invent multi-person teams in code/docs/README.
2. Prefer working, honest systems over overstated AI claims.
3. WhatsApp-style UX narrative is fine; the shipped client is a reliable web UI.
4. Cameroon context: bilingual FR/EN; institutional sources; local threat patterns.
5. Privacy by design: minimise PII; do not keep user media longer than needed.
6. Keep English primary in repo docs unless asked otherwise.
7. Never claim forensic certainty; default is `certainty: "none"`.

## Stack

- **Backend:** FastAPI (`backend/app/main.py`)
- **Frontend:** Static HTML/CSS/JS (`frontend/`)
- **Data:** `data/institutions.json`, `data/sources.json`, `data/lessons.json`
- **Samples:** `frontend/static/samples/`
- **Detection:** Heuristic adapters + trust fusion; real models only behind registry/checksums

## Important APIs

- `GET /health`
- `POST /api/v1/trust/assess`, `POST /api/v1/trust/assess/media`
- `POST /api/v1/analyze`
- Legacy checks still exist under `/api/v1/check/*`
- Incidents, analyst, NTOC, intel, evidence, announcements, governance, interop, SCIM, TAXII

## Coding rules

- Touch only what is needed; no drive-by refactors
- Match existing structure under `backend/app/`
- Add tests under `backend/tests/`
- Do not restore competition/pitch/jury assets or framing
- Commit only when the user asks

## Definition of done for readiness work

- Tests pass
- Docs mention current version/phase
- Soft-auth demo still works
- National profile remains fail-closed for secrets and auth
- Claims match what the code actually enforces
