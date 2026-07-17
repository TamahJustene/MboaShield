# ADR-0002: National TrustAssessment resource model

**Status:** Accepted  
**Date:** 2026-07-17  
**Pillar(s):** pillar-trust  
**Transformation phase:** T1 (2.1.0)

## Context

MboaShield exposes trust through several modalities (`/check/text`, `/check/media`, `/intelligence/analyze`, etc.) with per-modality risk scores and ad hoc JSON shapes. National infrastructure requires one **explainable** assessment pattern consumable by citizens, institutions, and partners, without breaking existing `/api/v1` check routes.

## Decision

1. Introduce a first-class **`TrustAssessment`** resource with fields: `object_type`, `object_id`, `score` (0–100 trust), `band` (`high` | `medium` | `low`), `signals[]`, `certainty`, `evidence_refs[]`, plus optional link to `verification_check_id`.
2. Add **`POST /api/v1/trust/assess`** and **`GET /api/v1/trust/assessments/{id}`** as the canonical trust API; existing check endpoints remain unchanged.
3. **`POST /trust/assess`** delegates to the same engine stack as today’s checks and intelligence fusion, then persists an assessment row when `persist=true` (default).
4. **`certainty`** defaults to `"none"` for all automated assessments; human workflow outcomes may reference assessments but do not auto-elevate certainty.
5. **Trust score** is the primary metric (higher = more trustworthy). Legacy check responses continue to expose `risk_score` / `risk_band` where they exist today.

## Consequences

- Positive: Partners integrate one schema; UI can render a unified trust panel; assessments auditable separately from raw checks.
- Negative: Dual persistence (checks + assessments) until a later phase optionally consolidates views.
- Mitigation: Bridge `object_type=verification_check` to rehydrate assessments from stored checks; link `verification_check_id` on new assessments.

## Alternatives considered

- **Replace checks with trust API only:** Rejected — breaks `/api/v1/check/*` contracts and competition demos.
- **TrustAssessment without persistence:** Rejected — national audit trail requires stored assessments.
