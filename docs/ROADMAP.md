# MboaShield Implementation Roadmap

**Today:** 16 July 2026  
**Owner:** Justene Nkwagoh Tamah  
**Repo:** https://github.com/TamahJustene/MboaShield

---

## Timeline at a glance

```
16 Jul -------- 22 Jul -------- 24 Jul -------- 27 Jul -------- 30 Jul -------- 31 Jul
  |               |               |               |               |               |
Sprint 1        SUBMIT         Shortlist       Bootcamp        PITCH           Awards
Build power     dossier        published       mentors         Grand Jury      Prize
```

---

## Sprint 1 ù **Make it real** (16ù18 July)

**Goal:** Close the gap between dossier promises and demo reality.

| # | Task | Output | Status |
|---|---|---|---|
| 1.1 | Audio / voice-note analyser | `POST /api/v1/check/audio` + UI panel | DONE |
| 1.2 | Source verification on claims | `verify` block in text response | DONE |
| 1.3 | Expand institution registry (15+) | `data/institutions.json` (17 entries) | DONE |
| 1.4 | Expand official sources corpus | `data/sources.json` | DONE |
| 1.5 | 5-scenario pitch demo button | Updated `app.js` | DONE |
| 1.6 | Tests for new services | `backend/tests/` (4 tests) | DONE |

**Done when:** Demo covers text, audio, image, impersonation, certificate ù all in one click.

---

## Sprint 2 ù **Get in the room** (19ù22 July)

**Goal:** Submit a dossier that gets you shortlisted.

| # | Task | Output | Status |
|---|---|---|---|
| 2.1 | Submit form + `MboaShield.pdf` | Confirmation email/screenshot | TODO |
| 2.2 | Public demo URL | Render / Railway / ngrok / GitHub Pages proxy | TODO |
| 2.3 | Record 90s backup demo video | `docs/demo_backup.mp4` (not in git) | TODO |
| 2.4 | Update dossier demo URL | Form + PDF if needed | TODO |
| 2.5 | French summary block on landing | UI + optional 1-page FR PDF | TODO |

**Done when:** Submission complete before **22 Jul 15:30** with working public link.

---

## Sprint 3 ù **Look like a winner** (23ù26 July)

**Goal:** Presentation quality matches ambition.

| # | Task | Output | Status |
|---|---|---|---|
| 3.1 | Mobile-first UI refresh | PWA-style layout, Cameroon colours | TODO |
| 3.2 | Pitch deck (8ù10 slides) | `docs/pitch_deck.pdf` or Google Slides | TODO |
| 3.3 | Marketing video 60ù90s | Required by Grand Jury rules | TODO |
| 3.4 | Architecture one-pager | `docs/ARCHITECTURE_ONE_PAGER.pdf` | TODO |
| 3.5 | Pitch rehearsal x10 | Timed script, FR + EN | TODO |
| 3.6 | Q&A cheat sheet | `docs/JURY_QA.md` | TODO |

**Done when:** You can pitch without looking at notes; video plays if demo fails.

---

## Sprint 4 ù **Win on stage** (27ù30 July)

**Goal:** Grand Jury leaves remembering MboaShield.

| # | Task | Output | Status |
|---|---|---|---|
| 4.1 | Bootcamp ù absorb mentor feedback | Updated demo only | TODO |
| 4.2 | Cut anything that crashes once | Stable build only | TODO |
| 4.3 | Final pitch (30 Jul) | Live demo + deck | TODO |
| 4.4 | Exposition day talking points | 30s + 2min versions | TODO |

**Done when:** Pitch ends with: *"MboaShield IS the 2026 theme."*

---

## Sprint 5 ù **After competition** (Aug 2026+)

Only if you win or want to scale ù not before pitch.

| Area | Direction |
|---|---|
| WhatsApp Business API | Wrap existing `/api/v1/*` endpoints |
| Real deepfake model | ONNX / HuggingFace, Cameroon fine-tune |
| SQLite + analytics | Usage metrics for B2G story |
| OAPI + CDEN | If prize unlocked |
| USSD gateway | Telco partnership |

---

## Build order (strict priority)

1. Features that appear **live on stage**  
2. Features that appear in **dossier / deck**  
3. Features that are **cool but risky** ù last or never before pitch  

---

## How to use this file

- Mark tasks `DONE` as you finish  
- Any AI agent: read `GOALS.md` + this file + `AI_BRIEF.md` before coding  
- Do **not** start Sprint 5 before Sprint 4 pitch is delivered  

---

## Current sprint focus

**Sprint 1 ù tasks 1.1 to 1.6**  
Next session: finish audio + source verification, then expand registry.
