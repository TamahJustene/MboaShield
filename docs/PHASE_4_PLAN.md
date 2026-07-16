# Phase 4 Plan - National Analytics

**Version target:** 0.8.0  
**Depends on:** Phase 3 (v0.7.0)  
**Status:** COMPLETE (v0.8.0)

## Why
Government operators need national situational awareness: threat trends, regional
pressure, response performance, AI quality signals, and citizen participation.

## In scope
1. Analytics aggregation service over checks, incidents, events, users, certificates
2. National Trust Dashboard API + UI
3. Threat / deepfake trends, regional heat map, incident timeline
4. Response-time metrics
5. AI accuracy proxy + optional analyst feedback labels
6. Citizen participation metrics

## Honesty
AI accuracy starts as feedback-driven plus disposition proxies (resolved vs dismissed).
It never claims ground-truth model accuracy without labeled feedback.

## Out of scope
- GIS map tiles / external map providers
- OAuth/MFA (Phase 5)
- Real-time streaming analytics
