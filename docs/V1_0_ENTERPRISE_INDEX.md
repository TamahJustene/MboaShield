# MboaShield v1.0 Enterprise Program — Index

**Status:** Phase 7 (NTOC) COMPLETE — v1.1.0  
**Application code:** Phases 6-7 shipped; Phase 8+ gated until started  
**Baseline product before Phase 6:** v0.9.0 (Phases 1-5)  
**Current product:** v1.1.0  
**Target:** National Digital Trust Platform suitable for multi-country government deployment  

**Non-negotiables:** Never rebuild; never break `/api/v1/*`; never mock/TODO; one phase at a time; production-ready only.

**Compliant intelligence (Phase 8):** Collection only via official APIs, licensed feeds, RSS, and other authorized/public interfaces. No ToS-violating scraping of Facebook, X, YouTube, Telegram, or similar platforms.

---

## Authoritative baseline (v0.9.0)

| Document | Role |
|---|---|
| [`PRODUCT_STATUS.md`](PRODUCT_STATUS.md) | What exists today |
| [`ACCESS_AND_CONFIG.md`](ACCESS_AND_CONFIG.md) | Who can access what + env knobs |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Current stack map |
| [`DEPLOY.md`](DEPLOY.md) | Deploy paths |
| [`../CHANGELOG.md`](../CHANGELOG.md) | Version history |

---

## v1.0 enterprise deliverables (this program)

| # | Document | Step |
|---|---|---|
| 1 | [`V1_0_ARCHITECTURE_REVIEW.md`](V1_0_ARCHITECTURE_REVIEW.md) | Architecture review (10 assessments) |
| 2 | [`V1_0_SYSTEM_DESIGN.md`](V1_0_SYSTEM_DESIGN.md) | Full system design + C4 + journeys |
| 3 | [`V1_0_THREAT_MODEL.md`](V1_0_THREAT_MODEL.md) | STRIDE + AI/identity risks + mitigations |
| 4 | [`V1_0_IMPLEMENTATION_ROADMAP.md`](V1_0_IMPLEMENTATION_ROADMAP.md) | Phases 6�15 with gates |

---

## Decision gate before Phase 7 code

Phases 6-7 complete (v1.1.0). Implementation of Phase 8 may begin only when explicitly started.

---

## Version mapping (planned)

| Phase | Planned product version | Theme |
|---|---|---|
| 6 | 1.0.0 | Enterprise Identity Platform |
| 7 | 1.1.0 | National Trust Operations Center |
| 8 | 1.2.0 | Threat Intelligence (compliant sources) |
| 9 | 1.3.0 | Digital Evidence Vault |
| 10 | 1.4.0 | Institution Administration |
| 11 | 1.5.0 | Verified Government Communications |
| 12 | 1.6.0 | Advanced AI Platform |
| 13 | 1.7.0 | Enterprise Infrastructure |
| 14 | 1.8.0 | Governance & Responsible AI |
| 15 | 1.9.0 | Documentation suite completion |

Patch versions (e.g. 1.0.1) reserved for fixes within a phase.
