# National pillar registry (v1.9 ? 2030)

Maps each **national platform** to current implementation, primary APIs, UI portals, and gap summary.

Legend: **Mature** = production-usable in gov profile with docs/tests · **Partial** = capability exists, not yet infrastructure-grade · **Gap** = not implemented

| Pillar | Current modules | API prefix (v1) | Portals today | Status | 2030 gap (summary) |
|---|---|---|---|---|---|
| **National Trust Platform** | `engines/*`, `trust_fusion`, `platform` checks, `intelligence` | `/check/*`, `/intelligence/*`, `/analyze` | `/`, citizen | Partial | Unified trust object model; score for all entity types; public trust verify API |
| **National Identity Platform** | `auth`, `admin_users`, `oauth`, `identity_store`, RBAC | `/auth/*`, `/admin/users`, OIDC/SAML/LDAP | `identity.html` | Partial | SCIM; national IdP production; institution identity graph |
| **National Threat Intelligence Platform** | `intel`, `intel_store`, connectors | `/intel/*` | `intel.html`, NTOC | Partial | STIX/TAXII export-import; national IoC hub; trust network exchange |
| **National Investigation Platform** | `cases`, `incident_workflow`, `government`, investigation UI | `/cases/*`, `/incidents/*` | `investigation.html`, analyst, reports | Partial | Judiciary portal; cross-agency case federation |
| **National Evidence Platform** | `vault_store`, `evidence`, S3/local | `/evidence/*` | via investigation | Partial | WORM/legal hold; national evidence index; chain-of-custody standards export |
| **National Government Communications Platform** | `announcements`, `public_verify`, signing | `/announcements/*`, `/verify/a/*` | announcements, verify | Mature (demo) | CAP emergency alerts; multi-ministry publish workflow |
| **National Analytics Platform** | `analytics`, national aggregates | `/analytics/*` | `national.html` | Partial | Real-time pipelines; sector dashboards (health, election, finance) |
| **National AI Platform** | `ai_platform`, `ai_store`, `services/ai` | `/ai-platform/*` | `ai-lab.html` | Partial | Continuous monitoring; federated eval; video/document engines live |
| **National Governance Platform** | `governance_store`, risk/cards/consent | `/governance/*` | `governance.html` | Partial | ISO/NIST-aligned control mapping; audit dashboards; DPIA records |
| **National Partner Platform** | `partners`, API keys, OAuth clients | `/partners/*`, `/oauth/*` | `identity.html` | Partial | Webhook event bus; developer portal; SLA tiers; rate plans |

---

## Cross-cutting: National Digital Trust Network

| Capability | Today | Target |
|---|---|---|
| Trust relationships between institutions | Implicit via institution registry | Explicit `trust_relationship` + policy |
| Secure exchange channels | Manual API calls | Authenticated exchange endpoints + audit |
| Shared workflows | Single-tenant incident flow | Cross-institution case handoff |
| Alert types (deepfake, fraud, IoC, advisory) | Partial (notifications, intel items) | Typed alert registry + CAP/STIX where applicable |

**Transformation phase:** T2 (see transformation plan).

---

## Cross-cutting: Interoperability

| Standard | Today | Target |
|---|---|---|
| OpenAPI | Yes (`/docs`, export script) | Versioned `/api/v2` when breaking; pillar tags |
| Webhooks | Notification URL env only | Outbound event catalog + signing |
| OAuth2 / OIDC / SAML | Implemented | Production IdP + partner consent |
| SCIM | No | User/group provisioning phase T5 |
| STIX/TAXII | No | Intel export/import phase T4 |
| CAP | No | Emergency advisory phase T4 |

---

## Backward compatibility rule

All transformation phases **preserve** existing `/api/v1/*` contracts unless a deprecation window and migration guide are published. New capabilities prefer **additive** routes or `/api/v1/trust-network/*`, `/api/v1/trust/*` namespaces.
