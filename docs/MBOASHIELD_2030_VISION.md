# MboaShield 2030 - National digital public infrastructure

**Status:** North-star architecture (Chief Architect Directive)  
**Baseline implementation:** v1.9.0 (Phases 6-15 complete)  
**Transformation plan:** [`NATIONAL_INFRASTRUCTURE_TRANSFORMATION_PLAN.md`](NATIONAL_INFRASTRUCTURE_TRANSFORMATION_PLAN.md)

---

## What MboaShield is

MboaShield is **not** a web application, an AI detector, or a public demo.

MboaShield is **national digital public infrastructure**: the trusted digital backbone through which governments, institutions, businesses, and citizens **verify digital trust** - communications, identities, media, evidence, AI-assisted analysis, and cyber incidents - across Cameroon and, by configuration, other nations.

---

## Mission (2030)

Operate as infrastructure a government could run for **twenty years**, eventually serving:

Presidency, PMO, National CERT, election bodies, law enforcement, judiciary, banks, telcos, hospitals, universities, media, emergency services, private sector, international partners, and **millions of citizens**.

---

## Design test (every component)

Before shipping any capability, answer:

1. **Why does it exist?**
2. **Which national capability does it enable?**
3. **Which institution uses it?**
4. **How does it integrate with the rest of the ecosystem?**
5. **Can another country deploy it without rewriting code?**
6. **Would this still make sense in ten years?**

If any answer is weak, **redesign** before coding.

---

## The ten national platforms (permanent pillars)

| Pillar | National capability |
|---|---|
| **National Trust Platform** | Unified explainable trust scoring for all object types |
| **National Identity Platform** | People, institutions, accounts, federation |
| **National Threat Intelligence Platform** | Compliant intel, IoC exchange, collaboration |
| **National Investigation Platform** | Cases, workflows, cross-agency coordination |
| **National Evidence Platform** | Custody, integrity, retention, legal export |
| **National Government Communications Platform** | Signed announcements, public verify, advisories |
| **National Analytics Platform** | National situational awareness, feedback loops |
| **National AI Platform** | Models, evaluation, calibration - human accountability |
| **National Governance Platform** | Risk, consent, compliance, model/dataset cards |
| **National Partner Platform** | APIs, OAuth, webhooks, B2B/B2G integration |

These are **platforms**, not optional features. Current code maps to them; gaps are closed in transformation phases (see plan).

---

## Portals (shared backend)

All portals consume the same Trust API (`/api/v1/*` today; versioned evolution under OpenAPI):

Citizen - Government - Institution - Analyst - Investigator - Judiciary - Partner - Media - Emergency - Developer

Today: static HTML consoles per persona. Target: portal shell + capability modules + hard auth in government profile.

---

## National Digital Trust Network

Institutions securely exchange (with policy and audit):

Threat intelligence - IoCs - Verified announcements - Deepfake/fraud/impersonation alerts - Emergency advisories - Risk bulletins - Digital evidence metadata - Case updates

**Target:** trust relationships, collaboration channels, cross-institution workflows. **Today:** intel + announcements + cases partially; network layer is a **planned transformation phase**.

---

## Digital trust score

Everything that can be assessed receives an **explainable** trust assessment:

People - institutions - announcements - documents - media - accounts - sites - apps - reports - cases - evidence - intel items

Rules (non-negotiable):

- Trust is **explainable** (signals, provenance, cards).
- Trust **never claims certainty** by default (`certainty: none`).
- Trust **links to evidence** where applicable.

---

## Interoperability

Prefer open standards: REST, OpenAPI, webhooks, OAuth2, OIDC, SAML, SCIM, STIX/TAXII (where applicable), CAP (alerts), JSON/CSV/PDF.

No proprietary formats when an open standard exists. **Do not claim ISO/NIST certification** unless independently achieved - **design for assessability**.

---

## AI strategy

AI **assists**; humans **decide**. Every model: model card, dataset card, version, metrics, limitations, bias notes, calibration, monitoring, rollback.

---

## Security & resilience

Zero trust direction: authenticate, authorize, audit, encrypt, least privilege, secret management, API monitoring.

HA, horizontal scale, DR, backups, geo-redundancy, observability, graceful degradation - phased via infrastructure program (Phase 13 foundation; 2030 phases extend).

---

## Development workflow (from this directive onward)

1. Review architecture, docs, dependencies, APIs, security, scale, interoperability.
2. Publish an **implementation proposal** in the transformation plan (or phase appendix).
3. Confirm internal consistency and backward compatibility.
4. Implement with quality gates (backend, UI, migration, tests, docs, deploy, manuals).

**Reject** implementations that do not advance national infrastructure.

---

## Related documents

| Document | Role |
|---|---|
| [`NATIONAL_INFRASTRUCTURE_TRANSFORMATION_PLAN.md`](NATIONAL_INFRASTRUCTURE_TRANSFORMATION_PLAN.md) | Gap analysis + phased execution |
| [`pillars/PILLAR_REGISTRY.md`](pillars/PILLAR_REGISTRY.md) | Pillar ? code ? API ? portal mapping |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Current technical architecture (v1.9) |
| [`V1_0_SYSTEM_DESIGN.md`](V1_0_SYSTEM_DESIGN.md) | C4 context and containers |
| [`V1_0_THREAT_MODEL.md`](V1_0_THREAT_MODEL.md) | STRIDE and AI risks |
| [`COMPLETE_USER_GUIDE.md`](COMPLETE_USER_GUIDE.md) | Operational testing today |
