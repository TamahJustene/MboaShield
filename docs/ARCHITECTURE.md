# MboaShield Architecture

## Current state (v0.7.0 - Phase 3 intelligence)

```text
Browser UI
  home case panel shows Explainable Trust Score
  analyst / citizen / institution consoles
        |
        v
FastAPI create_app()
  api/v1/auth.py
  api/v1/platform.py
  api/v1/government.py
  api/v1/intelligence.py
        |
  services/engines/
    text | image | audio | video*
    identity | document*
    network | source | behavior | metadata
    trust_fusion.py
  services/ai_analysis.py   preserves ai_analysis envelope
  detectors remain under services/*adapters and check modules
```

`*` scaffolded engines return `status=unsupported` until models are attached.

## Explainable Trust Score

1. Run applicable engines independently
2. Collect confidence, evidence, reasoning, risk, threats, recommendations
3. Fuse with weighted blend favoring highest risk
4. `trust_score = 100 - fused_risk`
5. Always include `certainty: none` and honesty note

## Backward compatibility

- `/api/v1/check/*` still return detector results + `ai_analysis`
- Additive `intelligence` snapshot on single checks
- `/api/v1/analyze` keeps `modules` + `overall`, adds `engines` + `trust_score`

## Next phases

- Phase 4: national analytics dashboards
- Phase 5: OIDC/MFA and partner APIs
