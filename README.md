# MboaShield

Sovereign AI shield against deepfakes, disinformation and digital identity theft  Made in Cameroon.

**Founder (solo):** Justene Nkwagoh Tamah · `tamahjustene45@gmail.com`  
**Competition:** National Best ICT Project  Digital Innovation Week (SIN) 2026  
**Pitch target:** 30 July 2026 · Bootcamp: 2729 July 2026 · Submit dossier by **22 July 2026 15:30**

## Quick start

```bash
cd mboashield
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Open http://127.0.0.1:8000  interactive demo UI.

## What the MVP does (pitch-ready)

1. **Claim check**  paste a WhatsApp rumour / text ? risk score + plain explanation + Cameroon sources
2. **Impersonation check**  compare an account/name against an institutional registry
3. **Media heuristics**  upload image ? lightweight synthetic-media risk signals (extensible to full ML)
4. **Mboa Ambassadors**  short digital-patriotism learning module + certificate stub

## Docs for humans & AI agents

| Doc | Purpose |
|---|---|
| [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) | Day-by-day plan to pitch |
| [`docs/AI_BRIEF.md`](docs/AI_BRIEF.md) | **Pass this to any AI** to continue correctly |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System shape |
| [`../MboaShield.pdf`](../MboaShield.pdf) | Competition dossier |

## License

Proprietary until competition  © Justene Nkwagoh Tamah / MboaShield Tech
