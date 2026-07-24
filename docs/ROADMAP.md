# MboaShield implementation roadmap

**Owner:** Justene Nkwagoh Tamah  
**Repo:** https://github.com/TamahJustene/MboaShield  
**Current release:** v2.8.0

---

## Status snapshot

| Track | Status |
|---|---|
| Enterprise phases 1–15 | Complete (historical) |
| MboaShield 2030 T0–T7 | Complete |
| Continuous improvement CI-1 | Complete |
| Product readiness CI-2+ | Active |

---

## Active focus — product readiness (CI-2+)

| # | Work | Outcome |
|---|---|---|
| R1 | Authorization audit | Privileged routes require auth when `AUTH_ENFORCE=true` |
| R2 | Tenant model | `tenant_id` columns, backfill, fail-closed RLS |
| R3 | Secrets hygiene | Distinct signing secrets; national profile from KMS |
| R4 | Browser smoke | Home demo, analyst transition, announcement verify |
| R5 | Bilingual UX | Complete EN/FR on portal bodies, not only chrome |
| R6 | Resilience evidence | Attach load results and one DR restore drill |
| R7 | Docs sync | OpenAPI export and manuals match v2.8 |

---

## Completed foundation (do not reopen unless needed)

- Multimodal trust assessments and guided citizen demo
- Incident workflow, NTOC, intel, investigation, evidence vault
- Institution portal, signed announcements, public verify
- Identity/MFA/OIDC scaffolding, partner keys, SCIM create, TAXII read
- Interop webhooks/STIX/CAP, country packs, sector modules
- Governance cards/controls/consent and certainty policy

---

## Current sprint focus

Execute **R1–R3** first: authorization, tenancy, and secrets. Those unlock a credible national pilot profile.
