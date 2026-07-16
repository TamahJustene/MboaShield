# Phase 2 Plan ù Government Workflows

**Version target:** 0.6.0  
**Depends on:** Phase 1 (v0.5.0) security + SQLAlchemy foundation  
**Status:** COMPLETE (v0.6.0)

## Why
Phase 1 hardened identity and persistence. Phase 2 turns incident reports into a national escalation workflow that analysts and institutions can operate, with citizen visibility.

## In scope
1. National incident workflow states + immutable event timeline
2. Transition API with validation and audit logging
3. Analyst queue + summary API and console UI
4. Institution create/update admin API + admin UI
5. Citizen dashboard API + UI (my checks, my reports)
6. Backward-compatible legacy statuses (`open`, `reviewing`, `resolved`, `dismissed`)

## Workflow
Citizen Report (`open`)
? AI Analysis (`ai_analysis`)
? Analyst Review (`analyst_review` / legacy `reviewing`)
? Institution Review (`institution_review`)
? Decision (`decision`)
? Public Advisory (`public_advisory`)
? Resolved (`resolved`)
? Archived (`archived`)

Terminal reject path: `dismissed` from early/mid stages.

## Affected areas
- `backend/app/db/models.py`, `session.py`
- `backend/app/services/incident_workflow.py` (new)
- `backend/app/repositories.py`, `schemas.py`
- `backend/app/api/v1/platform.py` (+ workflow/gov routers)
- Frontend: `analyst.html`, `citizen.html`, institution admin, reports updates
- Docs: PRODUCT_STATUS, CHANGELOG, ARCHITECTURE, Alembic 0002

## Out of scope
- Full national heat-map analytics (Phase 4)
- OAuth/MFA (Phase 5)
- Modular AI engine split (Phase 3)
