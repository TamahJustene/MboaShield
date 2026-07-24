# MboaShield goals - product readiness

**Owner:** Justene Nkwagoh Tamah  
**North star:** Make MboaShield a credible, deployable national digital trust platform for Cameroon.

---

## What "ready" means

| Goal | Target |
|---|---|
| **Reliable demos** | Guided citizen journey and ops portals work without silent failures |
| **Honest AI** | Scores are decision-support; `certainty: none` unless governed otherwise |
| **National workflows** | Incidents move through review states with audit trails |
| **Hardened deploy** | National profile uses hard auth, rotated secrets, Postgres, workers |
| **Tenant safety** | Fail-closed RLS after `tenant_id` columns exist and are backfilled |
| **Operator docs** | Guides match the live v2.8 APIs and screens |
| **Proof** | Tests, load patterns, and a recorded restore drill support claims |

---

## Near-term readiness backlog

1. Route authorization audit under `AUTH_ENFORCE=true`
2. Tenant columns + activate fail-closed Postgres RLS
3. Separate signing secrets from JWT; KMS-backed national secrets
4. Browser smoke/E2E for home, analyst, announcement verify
5. Finish EN/FR coverage on operational portals
6. Record load results and one restore drill
7. Regenerate OpenAPI manuals from the live contract

---

## Product tiers

### Tier A - Demo-stable
- Soft-auth public demo remains useful for exploration
- Guided demo never shows fake LOW scores on errors
- Hub links every real surface

### Tier B - Pilot-ready
- Hard auth on privileged routes
- Postgres + migrations verified
- National compose requires injected secrets
- Operator manuals accurate

### Tier C - National-candidate
- Tenant isolation enforced
- Measured resilience evidence
- Independent security and legal review
- Production hosting and RPO/RTO accepted

---

## Daily habit

1. Run `/health` and the guided demo once
2. Fix one readiness backlog item
3. Keep docs synchronized with code
