# AI Brief  MboaShield (pass this whole file to any AI agent)

## Identity
- **Product:** MboaShield  sovereign AI shield for Cameroon against deepfakes, disinformation, digital identity theft + digital patriotism education.
- **Solo founder:** Justene Nkwagoh Tamah (`tamahjustene45@gmail.com`), GitHub likely `TamahJustene`.
- **Competition:** MINPOSTEL SIN 2026  National Best ICT Project. Theme: protect cyberspace from AI excesses + promote digital patriotism.
- **Hard dates:** Dossier submit **22 Jul 2026 15:30**; Bootcamp **2729 Jul**; Final pitch **30 Jul**; Awards **31 Jul**.

## Non-negotiables
1. Solo founder product  do **not** invent multi-person teams in code/docs/README.
2. Prefer **working demo** over perfect ML. Pitch wins on /20 demonstration.
3. WhatsApp-first UX narrative, but ship a **reliable web UI** for the stage demo (WhatsApp Cloud API is optional later).
4. Cameroon context: bilingual FR/EN OK; institutional sources; WhatsApp/USSD story.
5. Privacy by design: minimise PII, no storing user media longer than needed for analysis.
6. Keep English primary in repo docs unless asked otherwise; competition PDF can be EN or FR.

## Current MVP stack
- **Backend:** FastAPI (`backend/app/main.py`)
- **Frontend:** Static HTML/CSS/JS served by FastAPI (`frontend/`)
- **Data:** `data/institutions.json`, `data/sources.json`, `data/lessons.json`
- **Detection (v0):** Deterministic heuristics + rules (rumour keywords, impersonation fuzzy match, image EXIF/quality proxies). Designed so real ML models can plug into `backend/app/services/` later without rewriting API contracts.

## API contracts (do not break without migrating clients)
- `GET /health` ? `{ "status": "ok", "version": "..." }`
- `POST /api/v1/check/text` body `{ "text": "...", "lang": "en"|"fr" }` ? risk report
- `POST /api/v1/check/impersonation` body `{ "name": "...", "handle": "..." }` ? match report
- `POST /api/v1/check/media` multipart `file` ? media risk report
- `GET /api/v1/ambassadors/lessons` ? lessons list
- `POST /api/v1/ambassadors/complete` body `{ "lesson_id": "...", "learner_name": "..." }` ? certificate stub

## Definition of Done for pitch MVP
- [ ] Demo runs offline on localhost with one command
- [ ] Three live scenarios < 90s: (1) viral false claim (2) fake ministry account (3) Ambassadors certificate
- [ ] Image upload returns a readable risk score + explanation
- [ ] FR + EN UI strings for core buttons
- [ ] README has exact run steps
- [ ] No secrets committed; `.env.example` only

## How to extend (priority order)
1. Hardening demo reliability (fixtures + offline samples)
2. Better claim verification RAG against `data/sources.json`
3. Optional Whisper/voice clone heuristics for audio
4. Optional WhatsApp Cloud API webhook wrapping same services
5. Fine-tuned vision model only after pitch-critical path is rock solid

## Coding rules for agents
- Touch only whats needed; no drive-by refactors
- Match existing structure under `backend/app/services/`
- Add tests under `backend/tests/` for scoring logic
- Never invent that the product is already commercialised at scale (competition eligibility)
- Commit messages: short, why-focused; only when user asks

## One-liner for the founders pitch
> MboaShield is not adjacent to the 2026 theme  it IS the theme: Cameroonian AI against AI abuses, for digital patriotism.
