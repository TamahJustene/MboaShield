# MboaShield

Sovereign digital trust platform against deepfakes, disinformation, and digital identity theft — Made in Cameroon.

**Founder:** Justene Nkwagoh Tamah — `tamahjustene45@gmail.com`  
**Repo:** https://github.com/TamahJustene/MboaShield  
**Live demo:** https://mboashield.onrender.com  
**Current release:** v2.8.0 (MboaShield 2030 T0–T7 + CI-1)

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

## What the product does

1. **Claim check** — paste a rumour / text → risk score, explanation, Cameroon sources
2. **Impersonation check** — compare an account against the institutional registry
3. **Media and audio checks** — synthetic-media and voice-clone risk signals
4. **Mboa Ambassadors** — digital-literacy learning modules and certificates
5. **National workflows** — incidents, analyst review, NTOC, intel, evidence, signed announcements
6. **Interoperability** — OpenAPI, webhooks, STIX/CAP, TAXII, SCIM, country packs

## Product readiness

See [`docs/PRODUCT_STATUS.md`](docs/PRODUCT_STATUS.md) for the current readiness baseline and next hardening work.

## Docs

| Doc | Purpose |
|---|---|
| [`docs/PRODUCT_STATUS.md`](docs/PRODUCT_STATUS.md) | Current product brief and readiness backlog |
| [`docs/MBOASHIELD_2030_INDEX.md`](docs/MBOASHIELD_2030_INDEX.md) | National infrastructure program index |
| [`docs/COMPLETE_USER_GUIDE.md`](docs/COMPLETE_USER_GUIDE.md) | Feature map and how to test |
| [`docs/E2E_WALKTHROUGH.md`](docs/E2E_WALKTHROUGH.md) | End-to-end system tour |
| [`docs/ACCESS_AND_CONFIG.md`](docs/ACCESS_AND_CONFIG.md) | Roles, auth, and configuration |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Layers, APIs, engines, workflow |
| [`docs/DEPLOY.md`](docs/DEPLOY.md) | Deploy and public demo |
| [`docs/manuals/README.md`](docs/manuals/README.md) | Role manuals for operators and auditors |
| [`docs/AI_BRIEF.md`](docs/AI_BRIEF.md) | Brief for AI agents working on the repo |

## Deploy

```bash
# Option A: Render — see docs/DEPLOY.md
# Option B: Quick tunnel
./scripts/public_tunnel.sh
```

Product hub: http://127.0.0.1:8000/static/hub.html

## License

Proprietary — (c) Justene Nkwagoh Tamah / MboaShield Tech
