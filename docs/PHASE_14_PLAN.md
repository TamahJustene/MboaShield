# Phase 14 - Governance

**Version:** 1.8.0  
**Status:** COMPLETE  

## Delivered

- Consent API for optional citizen features
- Risk register with `threat_model_ref` links (e.g. `TM-AI-OVERCONFIDENCE`)
- Model cards and dataset cards
- Responsible AI / privacy / compliance controls
- Compliance dashboard + recent audit snapshot
- UI: `/static/governance.html`
- APIs: `/api/v1/governance/*`

## Honesty rule preserved

Certainty policy remains `"none"` on model cards and compliance dashboard.

## Rollback

Set `GOVERNANCE_ENABLED=false`.
