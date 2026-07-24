# MboaShield v1.0 - Architecture Review

**Date:** 16 July 2026  
**Baseline:** Product v0.9.0 (Phases 1-5 complete, live at https://mboashield.onrender.com)  
**Authors (roles):** CTO - Chief Software Architect - Principal AI - Cybersecurity - DevSecOps - Cloud - Database - UX - Gov Digital Transformation - Digital Identity - AI Governance - Enterprise Solutions - Technical Writing  

**Code freeze:** No application code changes until [`V1_0_IMPLEMENTATION_ROADMAP.md`](V1_0_IMPLEMENTATION_ROADMAP.md) Phase 6 is explicitly started.

---

## 1. Executive Architecture Vision

MboaShield becomes a **configuration-driven National Digital Trust Platform**: a sovereign capability for detecting, investigating, explaining, and responding to AI-enabled threats, misinformation, deepfakes, impersonation, identity abuse, and coordinated online campaigns.

### Design thesis

1. **Preserve the working core** - FastAPI `create_app()`, `/api/v1/*`, SQLite/Postgres dual path, modular engines, incident workflow, soft/hard auth - are assets, not prototypes to discard.  
2. **Extend by modules** - New capabilities arrive as additive routers, services, tables, and UIs behind feature flags / env config.  
3. **Multi-country by configuration** - Country name, languages, IdP endpoints, region taxonomies, retention policies, threat-level thresholds, and branding live in config/tenant profiles - not forks.  
4. **Honest AI** - Heuristics and models never claim certainty; trust scores remain explainable and calibrated.  
5. **Government-grade identity** - Complete federation (OIDC/OAuth2/SAML/LDAP/AD), admin user lifecycle, sessions, devices, and enforced RBAC.  
6. **Compliant intelligence** - OSINT only through official APIs, RSS, and authorized feeds.  
7. **Evidence-grade operations** - Chain of custody, vault, signatures, and auditability for law enforcement and CERTs.  
8. **Operate as a national service** - NTOC dashboards, casework, notifications, institution health, observability, HA.

### Target stakeholders

National governments, ministries, CERTs, law enforcement, election commissions, banks, universities, telcos, healthcare, media, civil society, citizens, and international development partners.

---

## 2. Current Architecture Assessment

### What exists and works (reuse)

| Layer | Status | Evidence |
|---|---|---|
| App factory + middleware | Production-usable | CORS, rate limit, security headers, `/health` |
| Dual DB | Ready | SQLite default; Postgres via `DATABASE_URL`; Alembic 0001-0004 |
| RBAC model | Partial enforce | Roles/permissions defined; soft mode for demo |
| JWT + MFA TOTP | Working | Register/login/refresh; MFA challenge path |
| Partner API keys | Working | Hashed `msb_` keys, scopes, `X-API-Key` |
| Incident workflow | Working | Validated state machine + timeline |
| 10 engines + trust fusion | Working (8 active) | Video/document scaffolded honestly |
| Analytics APIs + national UI | Working | Aggregates + feedback labels |
| Static operator UIs | Working | Citizen, analyst, institutions, identity, national |
| CI | Working | pytest on push |
| Deploy | Demo-grade | Docker + Render free tier |

### Architectural style today

Monolithic modular FastAPI service with repository layer, service packages, and static HTML consoles. Not full Clean Architecture/DDD yet, but **clear seams** exist for incremental extraction (engines, workflow, auth, analytics).

### Strengths

- Backward-compatible API evolution across Phases 1-5  
- Soft/hard auth switch preserves guided demo while allowing lock-down  
- Explainable trust fusion with explicit `certainty: "none"`  
- Thin HTML UIs over real APIs (low coupling to a SPA framework)  

### Weaknesses (structural, not fatal)

- Large `repositories.py` / fat routers - cohesion pressure  
- Permissions defined but many routes ungated even when `AUTH_ENFORCE=true`  
- No tenant/country config object yet  
- OIDC callback incomplete (501 path)  
- No async job plane (all request-path work)  
- SQLite on live free tier = ephemeral data  
- Static UIs not auth-gated at HTTP layer  

---

## 3. Gap Analysis (vision vs v0.9.0)

| Capability | Today | Target (v1.x) | Gap severity |
|---|---|---|---|
| Enterprise identity (OIDC/SAML/LDAP/AD/SSO) | Scaffold OIDC + local JWT/MFA | Full federation + admin lifecycle | **Critical** (Phase 6) |
| User admin UI/API | DB role updates only | Full CRUD, invites, disable, audit | **Critical** |
| NTOC / investigation workspace | Analyst queue + national charts | Live threat level, cases, notes, assign | **High** (Phase 7) |
| Threat intel ingestion | None | Compliant collectors + correlation | **High** (Phase 8) |
| Evidence vault | Check JSON in DB | Hash, CoC, retention, export | **High** (Phase 9) |
| Institution admin platform | Registry CRUD | Domains, users, branding, keys, analytics | **Medium** (Phase 10) |
| Verified communications | Ambassadors cert stub | Signed announcements + QR verify | **Medium** (Phase 11) |
| Advanced AI runtime | Heuristics + adapters | ONNX/transformers registry + eval | **Medium** (Phase 12) |
| Enterprise infra | Single container | Redis/queue/object store/K8s/obs | **High** for national scale (Phase 13) |
| Governance suite | Honest AI posture | Model cards, consent, compliance UI | **Medium** (Phase 14) |
| Doc suite | Product/ops docs | Admin/dev/user/security manuals | **Medium** (Phase 15) |
| Multi-country config | Env-only Cameroon-centric | Tenant/country profiles | **High** (cross-cutting from Phase 6+) |

---

## 4. Technical Debt Assessment

| Debt item | Risk if ignored | Disposition |
|---|---|---|
| Soft auth default on -production- Render | Public abuse of gated ops APIs | Keep for demo flag; **gov profile** must enforce true |
| Ungated check/analyze under hard mode | Abuse / DoS / data pollution | Phase 6: selective gates + rate classes |
| No role management API | Ops error-prone (SQL) | Phase 6 deliverable |
| Fat repository module | Merge conflicts, test cost | Gradual split by domain (no big-bang) |
| `create_all` + Alembic dual path | Schema drift | Prefer Alembic as source of truth in gov deploys |
| Video/document engines stub | False expectation of coverage | Keep scaffolded status; Phase 12 upgrades |
| OIDC stub callback | Auth confusion | Phase 6 completes or clearly feature-flags off |
| Free-tier cold start / SQLite | Demo fragility | Phase 13 + DEPLOY gov profile |
| HTML consoles share no design system | UX inconsistency at NTOC scale | Phase 7+ shared CSS tokens, progressive enhancement |
| `TRUSTED_HOSTS` unused | Host header risk | Wire in Phase 6/13 middleware pass |

**Debt policy:** Pay down only when a phase touches that module. No drive-by rewrites.

---

## 5. Scalability Assessment

| Dimension | Current capacity | Bottleneck | Path |
|---|---|---|---|
| Concurrent HTTP | Single Uvicorn process (typical) | CPU-bound analyze | Workers + queue (Phase 13) |
| DB | SQLite write lock / single Postgres | Analytics scans | Indexes, read replicas later |
| Media analyze | In-request | Timeouts on large files | Async jobs + object storage |
| Multi-tenant countries | None | Config + data isolation | Tenant_id + RLS or schema strategy |
| Horizontal scale | Stateless app almost | Local uploads/SQLite | Object store + external DB |

**Verdict:** Adequate for national **pilot** and public demo. Inadequate for multi-ministry production without Phases 9 + 13.

---

## 6. Security Assessment

| Control | Present | Gap |
|---|---|---|
| Password hashing / strength | Yes | Recovery flow missing |
| Lockout | Yes | Policy not fully admin-configurable |
| MFA TOTP | Yes | Not mandatory for MFA_REQUIRED_ROLES |
| JWT short-lived + refresh | Yes | Session inventory / revoke-all missing |
| RBAC | Partial | Incomplete route coverage; no admin UI |
| API keys hashed | Yes | Rotation UX limited |
| Audit logs | Yes | Coverage incomplete for all mutations |
| Rate limit | Yes | Not identity-aware tiers |
| CORS * | Demo | Must narrow for gov |
| Encryption at rest | OS/volume only | Vault/KMS for evidence (Phase 9/13) |
| Federation | Incomplete | Phase 6 |
| Supply chain | requirements.txt + CI | SBOM, pin/audit (Phase 13/14) |

**Critical finding:** Live platform with `AUTH_ENFORCE=false` is intentional for demo but **must not** be marketed as government-hardened until locked profile is verified.

---

## 7. AI Capability Assessment

| Engine | Maturity | Honesty |
|---|---|---|
| Text / behavior / source / network / metadata / identity / image / audio | Heuristic-active | Appropriate for MVP |
| Video / document | Scaffolded | Correctly non-claiming |
| Trust fusion | Deterministic explainable | Keep; calibrate in Phase 12 |
| Certainty | Always none | Preserve forever as policy default unless calibrated model cards say otherwise |
| Model registry / monitoring | Absent | Phase 12 |
| Human feedback | Analytics labels only | Expand Phase 12/14 |

**AI governance stance:** Prefer false humility over false confidence. Never ship certainty claims for deepfake verdicts without evaluated models and human oversight paths.

---

## 8. Infrastructure Assessment

| Component | Today | Enterprise need |
|---|---|---|
| Compute | Render free Docker | Reserved capacity / K8s |
| DB | SQLite or optional Postgres | Managed Postgres HA |
| Cache / sessions | In-process | Redis |
| Jobs | None | RabbitMQ/Celery or equivalent |
| Object storage | Local filesystem uploads | S3-compatible |
| Observability | App logs | Prometheus/Grafana/Loki |
| Secrets | Env / Render generate | Vault/KMS |
| Multi-region | Single Frankfurt | Config per country region |

---

## 9. Deployment Assessment

| Path | Fit |
|---|---|
| Render free | Competition / public demo only |
| Docker Compose + Postgres | Ministry pilot |
| Kubernetes + Helm (Phase 13) | National production |
| Vercel proxy | Optional CDN for static; API remains origin |

**Requirement:** Maintain zero-friction `./scripts/run_demo.sh` forever. Add `deploy/gov` profile without removing demo profile.

---

## 10. Documentation Assessment

| Area | Status |
|---|---|
| Product status / access / architecture / deploy | Strong for v0.9 |
| OpenAPI | Auto via FastAPI |
| Admin / security / ops manuals | Incomplete (Phase 15) |
| Model / dataset cards | Absent (Phase 14) |
| Multi-country runbooks | Absent |

This review + design + threat model + roadmap close the **enterprise planning** documentation gap.

---

## Disposition lists (binding for all future phases)

### Already exists - reuse

- `create_app()`, `/api/v1` router composition, `deps.require_permission`  
- RBAC enums/permissions, JWT/MFA/partner key primitives  
- Incident workflow state machine  
- Engine registry + trust fusion  
- Analytics services and national UI patterns  
- Alembic chain, Docker, CI, Render blueprint  
- All citizen guided demo behaviors  

### Refactor (incremental, phase-scoped)

- Split `repositories.py` by domain when Phase 6/7/9 touch it  
- Complete OIDC (replace stub with real exchange) in Phase 6  
- Expand permission wiring without breaking soft-mode demo  
- Introduce `tenant` / `deployment_profile` config object  
- Extract shared frontend tokens for NTOC UIs  

### Remain untouched (unless bugfix)

- guided citizen demo scenario script and public home UX for the public demo  
- Soft-auth default for demo profile  
- Existing response shapes for `/check/*`, `/analyze`, ambassador flows  
- `certainty: "none"` policy on heuristic fusion  

### Deprecate (after replacement exists; never hard-delete without alias)

- OIDC -501 incomplete- behavior ? real callback or feature-flag disabled  
- Legacy `X-MboaShield-User-Id` as primary identity (keep as optional compat header)  
- Relying on SQL for role changes (after Phase 6 admin API)  
- Local-only evidence files once vault is live (migrate, don-t orphan)  

---

## Review conclusion

MboaShield v0.9.0 is a **credible national pilot chassis**, not yet an enterprise national platform. The correct path is **evolutionary modularization** through Phases 6-15, preserving all working capabilities, completing identity first, then operations, intelligence, evidence, and infrastructure.

**Next artifact:** [`V1_0_SYSTEM_DESIGN.md`](V1_0_SYSTEM_DESIGN.md)
