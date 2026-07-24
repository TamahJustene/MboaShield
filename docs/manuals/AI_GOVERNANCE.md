# AI Governance guide

**Version:** 1.9.0 - **Console:** `/static/governance.html` - **APIs:** `/api/v1/governance/*`

## Principles

1. **Honesty first** - never default to claiming certainty.
2. **Human in the loop** - public advisories require workflow decision states.
3. **Consent for optional use** - analytics/feedback/partner notify are opt-in.
4. **Document models and data** - model cards and dataset cards before enablement.
5. **Track residual risk** - risk register linked to threat-model refs (`TM-*`).

## Artifacts

| Artifact | Purpose |
|---|---|
| Model cards | Intended use, limitations, certainty policy |
| Dataset cards | Provenance for golden EN/FR sets |
| Risk register | Likelihood/impact/status/owner/mitigation |
| Controls | Responsible AI / privacy / compliance checklist |
| Consent records | Subject + feature + grant/revoke |

## Certainty policy

Product and model cards set `certainty_policy: none`. Calibration may expose `calibrated_score` for analysts; it does **not** upgrade certainty unless explicitly changed by policy and card revision.

## Evaluation

- Golden sets under `data/ai_golden_*.json`
- Run via AI lab or `/api/v1/ai-platform/evaluation/run`
- Latency budget: `AI_EVAL_LATENCY_BUDGET_MS`

## Compliance snapshot

`GET /api/v1/governance/compliance` returns open risks, implemented controls, card counts, and recent audit entries.

## Related controls in code

- Trust fusion: `backend/app/services/engines/` / trust fusion module
- Model registry checksums: Phase 12 AI store
- Threat model: [`../V1_0_THREAT_MODEL.md`](../V1_0_THREAT_MODEL.md)
- Phase plan: [`../PHASE_14_PLAN.md`](../PHASE_14_PLAN.md)
