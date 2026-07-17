# Phase 12 - Advanced AI Platform

**Version:** 1.6.0  
**Status:** COMPLETE  

## Delivered

- Model registry (`ai_model_registry`) with checksum verification
- Runtime adapters (heuristic + ONNX placeholder, always fallback-safe)
- `calibrated_score` on trust fusion when enough analyst feedback exists
- Golden evaluation datasets: `data/ai_golden_en.json`, `data/ai_golden_fr.json`
- Evaluation run persistence (`ai_evaluation_runs`)
- APIs under `/api/v1/ai-platform`
- UI: `/static/ai-lab.html`

## Honesty rule preserved

All outputs keep `certainty: "none"`; calibrated_score is optional decision support only.

## Rollback

Set `ADVANCED_AI_ENABLED=false`.
