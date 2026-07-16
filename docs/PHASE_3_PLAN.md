# Phase 3 Plan - Modular AI Intelligence Engines

**Version target:** 0.7.0  
**Depends on:** Phase 2 (v0.6.0)  
**Status:** COMPLETE (v0.7.0)

## Why
Government-grade trust platforms need separable, explainable intelligence modules rather than a single opaque detector. Phase 3 splits analysis into independent engines and fuses them into one Explainable Trust Score without claiming certainty.

## In scope
1. Engine contract: confidence, evidence, reasoning, risk_level, threat_category, recommendations
2. Engines: text, image, audio, video (scaffold), identity, document (scaffold), network, source, behavior, metadata
3. Trust fusion service producing Explainable Trust Score
4. Orchestrator used by existing enrich/analyze paths
5. Versioned intelligence API
6. Preserve existing `/api/v1/check/*` and `ai_analysis` response shapes

## Out of scope
- Real neural deepfake models / ONNX weights
- Full video pipeline decoding
- National analytics dashboards (Phase 4)
