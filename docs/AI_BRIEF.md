# AI Brief - MboaShield (pass this whole file to any AI agent)

## Identity
- **Product:** MboaShield - sovereign AI shield for Cameroon against deepfakes, disinformation, digital identity theft + digital patriotism education.
- **Solo founder:** Justene Nkwagoh Tamah (`tamahjustene45@gmail.com`), GitHub `TamahJustene`.
- **Repo:** https://github.com/TamahJustene/MboaShield
- **Competition:** MINPOSTEL SIN 2026 - National Best ICT Project. Theme: protect cyberspace from AI excesses + promote digital patriotism.
- **Hard dates:** Dossier submit **22 Jul 2026 15:30**; Bootcamp **27-29 Jul**; Final pitch **30 Jul**; Awards **31 Jul**.

## Non-negotiables
1. Solo founder product - do **not** invent multi-person teams in code/docs/README.
2. Prefer **working demo** over perfect ML. Pitch wins on /20 demonstration.
3. WhatsApp-first UX narrative, but ship a **reliable web UI** for the stage demo (WhatsApp Cloud API is optional later).
4. Cameroon context: bilingual FR/EN OK; institutional sources; WhatsApp/USSD story.
5. Privacy by design: minimise PII, no storing user media longer than needed for analysis.
6. Keep English primary in repo docs unless asked otherwise.

## Current MVP stack
- **Backend:** FastAPI (`backend/app/main.py`)
- **Frontend:** Static HTML/CSS/JS served by FastAPI (`frontend/`)
- **Data:** `data/institutions.json`, `data/sources.json`, `data/lessons.json`
- **Samples:** `frontend/static/samples/` for pitch media demo
- **Detection (v0):** Deterministic heuristics + rules. Plug real ML into `backend/app/services/` later without rewriting API contracts.

## API contracts (do not break without migrating clients)
- `GET /health` -> `{ "status": "ok", "version": "..." }`
- `POST /api/v1/check/text` body `{ "text": "...", "lang": "en"|"fr" }` -> risk report
- `POST /api/v1/check/impersonation` body `{ "name": "...", "handle": "..." }` -> match report
- `POST /api/v1/check/media` multipart `file` -> media risk report
- `POST /api/v1/check/audio` multipart `file` -> voice-clone risk report
- `GET /api/v1/ambassadors/lessons` -> lessons list
- `POST /api/v1/ambassadors/complete` body `{ "lesson_id": "...", "learner_name": "..." }` -> certificate stub

## Definition of Done for pitch MVP
- [x] Demo runs offline on localhost with one command
- [x] Five live scenarios < 90s: viral claim, impersonation, audio, image, certificate
- [x] Image upload returns a readable risk score + explanation
- [x] Audio / voice-note check endpoint + UI
- [x] Source verification on text claims
- [x] 17 Cameroon institutions in registry
- [x] FR + EN UI strings for core buttons
- [x] README has exact run steps
- [x] No secrets committed; `.env.example` only

## How to extend (priority order)
1. Public demo URL (Render / Railway / ngrok) for form submission
2. Screen-record backup MP4 for pitch
3. Mobile-first UI refresh (Sprint 3)
4. Pitch deck + marketing video
5. WhatsApp Cloud API webhook wrapping same services
6. Lightweight ONNX deepfake model after pitch path is stable

## Coding rules for agents
- Touch only what is needed; no drive-by refactors
- Match existing structure under `backend/app/services/`
- Add tests under `backend/tests/` for scoring logic
- Never invent that the product is already commercialised at scale (competition eligibility)
- Commit messages: short, why-focused; only when user asks (or when continuing active implementation)

## One-liner for the founder pitch
> MboaShield is not adjacent to the 2026 theme - it IS the theme: Cameroonian AI against AI abuses, for digital patriotism.
