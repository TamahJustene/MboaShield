# MboaShield

Sovereign AI shield against deepfakes, disinformation and digital identity theft - Made in Cameroon.

**Founder (solo):** Justene Nkwagoh Tamah - `tamahjustene45@gmail.com`
**Repo:** https://github.com/TamahJustene/MboaShield
**Competition:** National Best ICT Project - Digital Innovation Week (SIN) 2026
**Pitch target:** 30 July 2026 - Bootcamp: 27-29 July 2026 - Submit dossier by **22 July 2026 15:30**

## Quick start

```bash
cd mboashield
./scripts/run_demo.sh
```

Open http://127.0.0.1:8000

Or manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=. uvicorn backend.app.main:app --reload --port 8000
```

## What the MVP does (pitch-ready)

1. **Claim check** - paste a WhatsApp rumour / text -> risk score + plain explanation + Cameroon sources
2. **Impersonation check** - compare an account/name against an institutional registry
3. **Media heuristics** - upload image or click sample images -> synthetic-media risk signals
4. **Mboa Ambassadors** - short digital-patriotism learning module + certificate stub
5. **One-click demo** - "Run 90s pitch demo" button walks through all scenarios

## Docs for humans and AI agents

| Doc | Purpose |
|---|---|
| [`docs/PRODUCT_STATUS.md`](docs/PRODUCT_STATUS.md) | **Current full product brief — start here for next tasks** |
| [`docs/manuals/README.md`](docs/manuals/README.md) | **External-audit documentation suite (Phase 15)** |
| [`docs/E2E_WALKTHROUGH.md`](docs/E2E_WALKTHROUGH.md) | **End-to-end tour + improvement backlog** |
| [`docs/ACCESS_AND_CONFIG.md`](docs/ACCESS_AND_CONFIG.md) | **Who can access what + how to adjust roles/env** |
| [`docs/V1_0_ENTERPRISE_INDEX.md`](docs/V1_0_ENTERPRISE_INDEX.md) | **v1.0 enterprise review, design, threat model, roadmap** |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Layers, APIs, engines, workflow |
| [`docs/DEPLOY.md`](docs/DEPLOY.md) | Public demo URL (Render / tunnel) |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Sprint plan to pitch day |
| [`docs/GOALS.md`](docs/GOALS.md) | North-star score targets |
| [`docs/PITCH_DECK.md`](docs/PITCH_DECK.md) | 8-slide pitch script |
| [`docs/JURY_QA.md`](docs/JURY_QA.md) | Q&A cheat sheet |
| [`docs/AI_BRIEF.md`](docs/AI_BRIEF.md) | Pass to any AI agent |
| [`frontend/static/pitch.html`](frontend/static/pitch.html) | Printable pitch deck in browser |

## Deploy public demo (for competition form)

```bash
# Option A: Render (stable URL) - see docs/DEPLOY.md
# Option B: Quick tunnel
./scripts/public_tunnel.sh
```

Pitch deck in browser: http://127.0.0.1:8000/static/pitch.html

## License

Proprietary until competition - (c) Justene Nkwagoh Tamah / MboaShield Tech
