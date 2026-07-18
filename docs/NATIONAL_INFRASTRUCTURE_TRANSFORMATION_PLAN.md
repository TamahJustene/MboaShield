# National Infrastructure Transformation Plan

**Program:** MboaShield 2030
**Baseline:** v1.9.0 (monolith Trust API + static portals)
**Vision:** [`MBOASHIELD_2030_VISION.md`](MBOASHIELD_2030_VISION.md)
**Pillar map:** [`pillars/PILLAR_REGISTRY.md`](pillars/PILLAR_REGISTRY.md)
**Rule:** Preserve `/api/v1` stability; additive evolution; no big-bang rewrite.

---

## 1. Executive summary

The current platform is a **credible foundation** for national infrastructure: ten engine families, incident workflow, NTOC, intel, vault, signed comms, AI registry, governance, metrics, Helm/gov compose, and 80+ automated tests. It is still **packaged and experienced** too much like a demo web app (soft auth, static HTML silos, SQLite on public Render).

The transformation reframes the **same codebase** into **ten national platforms** and a **National Digital Trust Network**, without discarding what works. Execution is **eight transformation phases (T0-T7)** over multiple releases (2.0.x+), each passing the [quality gate](#7-quality-gate-checklist).

---

## 2. Gap analysis (current -> 2030)

| Dimension | Current (v1.9) | Target (2030) | Severity |
|---|---|---|---|
| **Product framing** | Demo + competition UX | DPI / national service | High (narrative + portals) |
| **Trust model** | Per-modality scores | Universal explainable trust objects | High |
| **Collaboration** | Single-org workflows | National trust network + exchange | High |
| **Portals** | 17 disconnected HTML apps | Portal framework, shared auth shell | Medium |
| **Identity** | MFA/OIDC/SAML ready, soft demo | Zero-trust default in gov; SCIM | High |
| **Intel interoperability** | Compliant ingest | STIX/TAXII + IoC hub | Medium |
| **Events** | Webhook env var | Event bus + signed webhooks | Medium |
| **Scale** | Monolith + optional workers | Multi-region HA, proven load | High |
| **Sector coverage** | Generic | Election, health, finance modules (config) | Medium |
| **International deploy** | Single tenant config | Country pack (tenant, legal, IdP templates) | Medium |
| **Assurance** | Threat model + governance | Control mapping to ISO/NIST (assessable) | Medium |
| **AI** | Heuristic + registry | Monitored models + human-only decisions | Ongoing |

**Strengths to preserve:** ordered review workflow, `certainty: none`, evidence custody, signed announcements, OpenAPI, Alembic, RBAC, partner keys, and phase documentation discipline. Human accountability depends on hard authentication plus operating controls.

---

## 3. Target logical architecture (2030)

```text
                    [ Portals: Citizen | Gov | Institution | Analyst | ... ]
                                        |
                              API Gateway / WAF (gov)
                                        |
         +------------------------------+------------------------------+
         |              Trust API (versioned OpenAPI)                   |
         +------------------------------+------------------------------+
         | Trust | Identity | Intel | Investigation | Evidence | Comms |
         | Analytics | AI | Governance | Partner | Trust Network        |
         +------------------------------+------------------------------+
                    |              Async workers / event bus
                    v
         PostgreSQL (primary) | Redis | Object store | Observability
                    |
         External: IdP | STIX feeds | CAP distribution | Partner webhooks
```

**Implementation strategy:** Evolve monolith **modularly** (Python packages per pillar) until metrics justify service extraction (already anticipated in system design).

---

## 4. Transformation phases

### T0 - Alignment & governance of architecture (2.0.0)

**Goal:** Lock north star; no user-visible breakage.

| Deliverable | Action |
|---|---|
| Vision + plan | This document + `MBOASHIELD_2030_VISION.md` + pillar registry |
| Architecture | Update `ARCHITECTURE.md` with pillar view |
| API taxonomy | OpenAPI tags grouped by national platform |
| ADR process | `docs/adr/README.md` - architecture decision records |
| Config | `COUNTRY_PACK=cm` tenant template (env + docs) |

**Quality gate:** Docs + OpenAPI tag pass + CI green.

---

### T1 - National Trust Object Model (2.1.0)

**Goal:** One explainable trust assessment pattern for all types.

| Deliverable | Action |
|---|---|
| Schema | `TrustAssessment` resource: `object_type`, `object_id`, `score`, `band`, `signals[]`, `certainty`, `evidence_refs[]` |
| API | `POST /api/v1/trust/assess`, `GET /api/v1/trust/assessments/{id}` |
| Bridge | Wrap existing checks + intelligence + future types |
| UI | Home + citizen show unified trust panel (backward compatible fields) |

**Institution:** CERT, citizens, partners (via API).

---

### T2 - National Digital Trust Network (2.2.0)

**Goal:** Institutions collaborate with policy and audit.

| Deliverable | Action |
|---|---|
| Models | `trust_relationship`, `exchange_channel`, `shared_alert` |
| API | `/api/v1/trust-network/relationships`, `/exchange/*` |
| Alerts | Typed: impersonation, deepfake, fraud, ioc, advisory |
| UI | Institution portal: "trusted partners" + share alert |

**Institution:** MINPOSTEL/CERT, banks, telcos (pilot).

---

### T3 - Portal platform (2.3.0)

**Goal:** Systems not pages; shared shell.

| Deliverable | Action |
|---|---|
| Shell | `portal-shell.js` - auth, nav, tenant, i18n FR/EN |
| Migrate | Analyst + NTOC + institution first |
| Developer portal | `/static/developer.html` - keys, webhooks, OpenAPI link |

**Not:** Rewrite all 17 pages in one release - incremental.

---

### T4 - Interoperability layer (2.4.0)

**Goal:** National systems consume MboaShield as a service.

| Deliverable | Action |
|---|---|
| Webhooks | Outbound events catalog + HMAC signatures + retry |
| STIX/TAXII | Intel export bundle (read-only pilot) |
| CAP | Emergency advisory export from `public_advisory` workflow |
| CSV/PDF | National report exports (existing patterns extended) |

---

### T5 - Zero-trust & identity scale (2.5.0)

**Goal:** Government-grade default.

| Deliverable | Action |
|---|---|
| Auth | `AUTH_ENFORCE=true` profile documented as national default |
| SCIM | Read-only SCIM users stub -> full provisioning |
| RLS | Postgres row-level security by `tenant_id` / institution |
| Secrets | KMS integration guide; no keys in env in prod doc |

---

### T6 - Resilience and scale patterns (2.6.0)

**Goal:** Provide repeatable load scenarios, HA patterns, and DR targets; record measured production results in a later validation phase.

| Deliverable | Action |
|---|---|
| Load tests | k6/Locust scenarios: trust assess, verify announcement |
| HA | Helm multi-AZ doc + Postgres HA pattern |
| DR | RPO/RTO runbook in operations manual |
| DR drill | Documented restore test |

---

### T7 - Sector packs & international deploy (2.7.0)

**Goal:** Another country without rewrite.

| Deliverable | Action |
|---|---|
| Country pack | `deploy/country-packs/{cm,template}/` - legal, institutions seed, IdP |
| Sector config | Election / health / finance dashboard toggles |
| Control mapping | Governance controls -> ISO/NIST framework IDs (assessable) |

---

## 5. What we will NOT do

- Break `/api/v1` without deprecation policy.
- Replace human workflow gates with AI auto-publish.
- Claim ISO/NIST certification without audit.
- Microservice split before load evidence.
- Proprietary alert formats where STIX/CAP exist.

---

## 6. Immediate next step (recommended)

**Program baseline complete:** Transformation phases **T0-T7** (releases 2.0.0-2.7.0) are delivered.

**CI-1 (2.8.0)** added TAXII read pilot, SCIM user create, and additional portal-shell migrations.

Further work is continuous improvement (CI-2+): SCIM PATCH/DELETE, TAXII write, live DR drills.


---

## 7. Quality gate checklist

No transformation phase closes until:

- [ ] Working backend (feature-flagged if needed)
- [ ] Working frontend or API-only with manual
- [ ] Alembic migration (if persistent)
- [ ] Automated tests (unit + API)
- [ ] Performance spot-check (if hot path)
- [ ] Security review (threat model delta)
- [ ] `ARCHITECTURE.md` + pillar registry update
- [ ] `ACCESS_AND_CONFIG.md` + deploy notes
- [ ] OpenAPI export regenerated
- [ ] User / admin / developer manual sections updated
- [ ] CHANGELOG + version bump

---

## 8. Version roadmap (indicative)

| Release | Phase | Theme |
|---|---|---|
| 1.9.x | - | Stable demo + guides (today) |
| 2.0.0 | T0 | 2030 architecture alignment |
| 2.1.0 | T1 | National trust object model |
| 2.2.0 | T2 | Trust network |
| 2.3.0 | T3 | Portal platform |
| 2.4.0 | T4 | Interoperability |
| 2.5.0 | T5 | Zero-trust identity |
| 2.6.0 | T6 | Load, HA, and DR patterns |
| 2.7.0 | T7 | Country packs |
| 2.8.0 | CI-1 | TAXII read, SCIM create, portal-shell expansion |

---

## 9. Acknowledgment

Transformation execution begins when stakeholders accept T0 scope. Until then, treat this plan as the **single source of truth** for architectural decisions per the Chief Architect Directive.

**Founder / architect:** Justene Nkwagoh Tamah
**Product:** MboaShield - National Digital Trust Infrastructure
