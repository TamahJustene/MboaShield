# MboaShield — Product status

**Baseline shipped:** v2.8.0 (T0–T7 + CI-1)  
**Strategic program:** MboaShield 2030 — National Digital Public Infrastructure  
**Live demo:** https://mboashield.onrender.com

---

## Current product

MboaShield is a working national digital trust prototype with:

- Multimodal trust assessments (text, identity, audio, image)
- Human-review incident workflow, NTOC, investigation, and evidence vault
- Institution registry, portal, and signed government announcements
- Identity, MFA/OIDC scaffolding, partner keys, SCIM create, TAXII read
- Interoperability (webhooks, STIX, CAP, CSV), country packs, sector modules
- Governance controls, model cards, consent, and certainty policy (`none` by default)

Start here for operators: [`COMPLETE_USER_GUIDE.md`](COMPLETE_USER_GUIDE.md)  
Start here for architecture: [`MBOASHIELD_2030_INDEX.md`](MBOASHIELD_2030_INDEX.md)

---

## Readiness baseline (honest)

| Area | Status |
|---|---|
| Citizen and ops demos | Working on soft-auth demo profile |
| API surface | Broad `/api/v1` + TAXII/SCIM pilots |
| Automated tests | Backend pytest suite green locally |
| Hard auth on all sensitive routes | Incomplete — still required |
| Tenant RLS with real columns | Template only — fail-closed until backfill |
| Durable Postgres / workers | Available as profiles, not default demo |
| Measured load / DR drill evidence | Patterns shipped; measured proof pending |
| Full bilingual UI | Partial (nav/titles; body content incomplete) |
| Independent security/legal audit | Not done |

---

## Next focus (product readiness)

1. Complete route authorization audit under `AUTH_ENFORCE=true`
2. Add/backfill `tenant_id` and activate fail-closed Postgres RLS
3. Separate signing secrets from JWT; require KMS-backed secrets in national profile
4. Browser smoke/E2E for home demo, analyst workflow, announcement verify
5. Finish EN/FR coverage on operational portals
6. Record load-test results and one restore drill against a durable environment
7. Export fresh OpenAPI manuals from the live v2.8 contract

---

## Key surfaces

| Surface | Path |
|---|---|
| Citizen home / guided demo | `/` |
| Product hub | `/static/hub.html` |
| Analyst console | `/static/analyst.html` |
| NTOC | `/static/ntoc.html` |
| Governance | `/static/governance.html` |
| Developer portal | `/static/developer.html` |
| API docs | `/docs` |
| Health | `/health` |

See [`CHANGELOG.md`](../CHANGELOG.md).
