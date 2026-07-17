# ADR-0008: Country packs and sector modules

**Status:** Accepted  
**Date:** 2026-07-17  
**Pillar(s):** All (internationalization / analytics)  
**Transformation phase:** T7 (2.7.0)

## Context

MboaShield must deploy to another country without rewrite, and expose sector-focused dashboards (election, health, finance) as config toggles. Governance controls need assessable ISO/NIST mappings without claiming certification.

## Decision

1. Formalize **country packs** under `deploy/country-packs/{id}/` with `pack.json` (legal, IdP, locales, institutions seed, default sectors).
2. Load active pack via `COUNTRY_PACK` and expose `GET /api/v1/country-pack`.
3. Enable sectors with `SECTORS_ENABLED=election,health,finance` (comma list); expose `GET /api/v1/sectors` and a sector dashboard UI.
4. Map governance controls to **ISO 27001 / NIST CSF** control IDs in code (`CONTROL_FRAMEWORK_MAP`); expose `GET /api/v1/governance/framework-map`. Mapping is **assessable**, not certified.

## Consequences

- Positive: New country = pack copy + env; sectors feature-flagged.
- Negative: Institution seed still Cameroon-centric until a pack ships its own JSON.
- Mitigation: Template pack documents required files; CM pack is the reference.

## Alternatives considered

- **Hardcode sectors in UI only:** Rejected - national APIs must advertise enabled sectors.
- **Claim ISO certification:** Rejected - mapping only until audit.
