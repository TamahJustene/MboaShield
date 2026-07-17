# MboaShield — Presenter guide (how to explain everything)

**Founder:** Justene Nkwagoh Tamah  
**Event:** SIN 2026 — National Best ICT Project  
**Time limit:** 3 minutes speaking + live demo  
**Deck file:** Download from https://mboashield.onrender.com/static/presentations.html  
**Regenerate deck:** `python scripts/generate_presentation.py`

**Rule:** Show the demo before deep technology. Honest about prototype stage; strong on impact and sovereignty.

---

## 1. One-sentence pitch

MboaShield is a Made-in-Cameroon national digital trust platform that helps citizens detect deepfakes, scams, and fake official accounts on WhatsApp-style channels, escalates incidents to human analysts, and trains Mboa Ambassadors in digital patriotism.

---

## 2. Slide-by-slide script (9 slides)

### Slide 1 — Title (15 sec)

> "Good morning. I am Justene Nkwagoh Tamah. I built MboaShield alone — a sovereign AI shield for Cameroon, aligned with the 2026 theme: protecting cyberspace from AI excesses while promoting digital patriotism."

### Slide 2 — Problem (20 sec)

> "Every day on WhatsApp we see fake minister messages, voice clones asking for MoMo, and deepfake images. Youth forward before verifying. That creates fraud, panic, and lost trust in the State."

### Slide 3 — Solution (15 sec)

> "MboaShield detects synthetic media, verifies rumours, flags fake official accounts, and trains Mboa Ambassadors. It is bilingual, privacy-aware, and designed for Cameroon — not a copy-paste of foreign tools."

### Slide 4 — Live demo (90 sec) **MOST IMPORTANT**

Do not read bullets — **do the demo**:

1. Open **mboashield.onrender.com**
2. Click **Run Grand Jury demo (90s)**
3. While it runs, say one line per step:
   - "Here a viral rumour gets a risk score and source check."
   - "Here a fake ministry-style account is compared to our institution registry."
   - "Here a voice note is flagged for clone risk."
   - "Here an image gets synthetic-media signals in plain language."
   - "Here digital patriotism ends with an Ambassador certificate."

If demo fails: use manual samples on each panel (pre-loaded text in guide).

### Slide 5 — Platform depth (20 sec)

> "Behind the demo is a full national platform: incident workflow with human gates, NTOC operations, evidence vault, signed government announcements, AI governance with model cards, and certainty never claimed by default."

### Slide 6 — Innovation (20 sec)

> "Multimodal AI — text, audio, image, identity — plus 17 institutions in registry. We are honest: heuristic engines today with a path to checksum-verified models. The differentiator is local context and civic mission."

### Slide 7 — Impact (15 sec)

> "Citizens get free checks. Schools get Ambassadors. Media and banks can use APIs. Government gets registry and verified comms. This is digital patriotism as software, not a slogan."

### Slide 8 — Business (15 sec)

> "Free for citizens; Pro and Enterprise tiers for institutions; Ambassador packs for schools. Year one targets pilots and sustainable revenue while keeping the citizen tier free."

### Slide 9 — Ask (15 sec)

> "I ask for the Special Prize of the President of the Republic to industrialise MboaShield nationally, scale the identity registry, and train fifty thousand Ambassadors in year one. MboaShield is not adjacent to the theme — it is the theme. Thank you."

---

## 3. Demo backup plan

| Failure | Backup |
|---|---|
| Render sleeping | Open `/health` 60s before; rehearse locally `./scripts/run_demo.sh` |
| Network down | Screen recording from rehearsal |
| One modality fails | Skip to next panel; mention "multimodal redundancy" |
| Low score on sample | Explain decision-support; show HIGH on stronger sample text |

Sample high-risk text: `URGENT send MoMo now official minister order`

---

## 4. How to explain "AI" to jury

- We do **not** claim forensic proof (`certainty: none`).
- Scores help **prioritize** attention; humans decide advisories.
- Golden EN/FR evaluation sets regression-test the engine.
- Governance page shows risk register and model cards — responsible AI.

---

## 5. How to explain architecture in one minute

> "FastAPI backend, static web UI, SQLite on demo Render, Postgres for government deploy. Optional Celery workers, Prometheus metrics, Helm chart for scale. Same API from citizen check to national analytics."

Point experts to `/docs` and `docs/manuals/`.

---

## 6. Q&A quick answers

| Question | Answer |
|---|---|
| False positives? | Human review before institutional alerts; thresholds + analyst feedback |
| vs Meta/Google? | Local registry, WhatsApp UX, FR/EN, civic education, sovereign hosting path |
| Why free? | Adoption and trust; B2B/B2G pays for scale |
| Solo founder? | Prize funds first hires: annotator + part-time AppSec |
| Production ready? | Demo-ready v1.9; government profile adds auth, Postgres, workers |
| Data privacy? | Minimize PII; consent for optional features; vault retention policies |

Full table: [`JURY_QA.md`](JURY_QA.md)

---

## 7. What to open if jury asks "show me X"

| They ask | Open |
|---|---|
| Everything | `/static/hub.html` |
| National view | `/static/national.html` |
| Analyst workflow | `/static/reports.html` + `/static/analyst.html` |
| Verified ministry message | `/static/announcements.html` + verify |
| AI governance | `/static/governance.html` |
| Technical API | `/docs` |

Full steps: [`COMPLETE_USER_GUIDE.md`](COMPLETE_USER_GUIDE.md)

---

## 8. Rehearsal schedule (recommended)

| When | Task |
|---|---|
| Daily | Run 90s demo twice; time under 3:00 with slides |
| T-2 days | Download PPT; test on presentation laptop |
| T-1 day | Record backup video; update FORM_ANSWERS URL |
| Pitch day | Wake Render; hub + home open in tabs |

---

## 9. Files you carry

1. **MboaShield_SIN2026.pptx** (USB + email backup)
2. **COMPLETE_USER_GUIDE.md** PDF (optional print)
3. **MboaShield.pdf** dossier (competition submission)
4. Live URL on phone hotspot as backup

---

**Close line (memorize):**  
*"MboaShield is not adjacent to the 2026 theme — MboaShield IS the theme."*
