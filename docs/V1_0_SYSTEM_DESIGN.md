# MboaShield v1.0 — System Design

**Baseline:** v0.9.0 · **Program index:** [`V1_0_ENTERPRISE_INDEX.md`](V1_0_ENTERPRISE_INDEX.md)  
**Review:** [`V1_0_ARCHITECTURE_REVIEW.md`](V1_0_ARCHITECTURE_REVIEW.md)

This document is the target architecture for Phases 6–15. Implementation must **extend** the current FastAPI monolith modularly; extraction to microservices is optional and only after Phase 13 proves scale need.

---

## 1. System Context (C4 Level 1)

```mermaid
C4Context
title MboaShield National Digital Trust Platform — System Context
Person(citizen, "Citizen", "Reports threats, verifies claims, learns")
Person(analyst, "CERT / Analyst", "Investigates incidents and cases")
Person(instAdmin, "Institution Admin", "Manages org identity and announcements")
Person(govAdmin, "National Admin", "Identity, policy, governance")
Person(partnerOp, "Partner Operator", "Banks, telcos, NGOs via API")
System(mboa, "MboaShield", "Detect, explain, investigate, respond to AI-enabled digital threats")
System_Ext(idp, "National / Enterprise IdP", "OIDC, SAML, LDAP/AD")
System_Ext(feeds, "Authorized Intel Sources", "Official APIs, RSS, licensed feeds")
System_Ext(storage, "Object Storage / KMS", "Evidence blobs and keys")
System_Ext(notify, "Notification Channels", "Email, SMS gateway, webhooks")
Rel(citizen, mboa, "Uses web / future WhatsApp")
Rel(analyst, mboa, "NTOC consoles")
Rel(instAdmin, mboa, "Institution portal")
Rel(govAdmin, mboa, "Admin + governance")
Rel(partnerOp, mboa, "HTTPS + API keys / OAuth")
Rel(mboa, idp, "Federated login")
Rel(mboa, feeds, "Pull authorized intelligence")
Rel(mboa, storage, "Store evidence")
Rel(mboa, notify, "Alerts")
```

### Justification

Single platform boundary keeps deployment simple for ministries while exposing clear external dependencies (IdP, storage, compliant feeds). Multi-country = multiple deployments or multi-tenant config inside the same boundary.

---

## 2. Container Diagram (C4 Level 2)

```mermaid
C4Container
title MboaShield — Containers (target after Phase 13; today = single API container)
Person(user, "Users", "All personas")
Container(web, "Web Consoles", "Static HTML/JS", "Citizen, Analyst NTOC, Institution, Admin")
Container(api, "Trust API", "FastAPI", "Auth, workflow, AI, analytics, vault APIs")
Container(worker, "Async Workers", "Celery", "Intel ingest, heavy AI, retention jobs")
ContainerDb(db, "Primary DB", "PostgreSQL", "Transactional state")
ContainerDb(redis, "Cache / Broker assist", "Redis", "Sessions, rate, queues assist")
ContainerDb(mq, "Message Broker", "RabbitMQ", "Job dispatch")
ContainerDb(obj, "Object Store", "S3-compatible", "Evidence media")
Container(obs, "Observability", "Prometheus/Grafana/Loki", "Metrics logs traces")
System_Ext(idp, "IdP")
Rel(user, web, "HTTPS")
Rel(web, api, "JSON /api/v1")
Rel(api, db, "SQL")
Rel(api, redis, "Session/cache")
Rel(api, mq, "Enqueue")
Rel(worker, mq, "Consume")
Rel(worker, db, "SQL")
Rel(worker, obj, "Read/write")
Rel(api, obj, "Presign/store")
Rel(api, idp, "OIDC/SAML")
Rel(api, obs, "Expose metrics")
Rel(worker, obs, "Expose metrics")
```

**Today (v0.9):** `web` + `api` colocated in one Docker image; SQLite or Postgres; no worker/redis/mq/obj. Phases add containers without removing the monolith entrypoint until K8s chart lands.

---

## 3. Component Diagram (C4 Level 3) — Trust API

```mermaid
flowchart TB
  subgraph API["Trust API process"]
    MW[Middleware: CORS, rate, security headers]
    RAuth[auth router]
    RPart[partners router]
    RPlat[platform router]
    RGov[government router]
    RIntel[intelligence router]
    RAnal[analytics router]
    RCase[cases router - Phase 7]
    RFeed[intel_feeds router - Phase 8]
    RVault[evidence router - Phase 9]
    RInst[institution_admin router - Phase 10]
    RComm[communications router - Phase 11]
    RGovn[governance router - Phase 14]
    Deps[deps: JWT / API key / RBAC]
    SvcAuth[Identity services]
    SvcWF[Incident workflow]
    SvcAI[Engine registry + fusion]
    SvcAn[Analytics]
    SvcCase[Casework]
    SvcFeed[Feed connectors - compliant]
    SvcVault[Evidence vault]
    SvcComm[Signed communications]
    Repo[Repositories / UoW]
  end
  DB[(PostgreSQL)]
  MW --> Deps
  Deps --> RAuth & RPart & RPlat & RGov & RIntel & RAnal & RCase & RFeed & RVault & RInst & RComm & RGovn
  RAuth --> SvcAuth
  RGov --> SvcWF
  RIntel --> SvcAI
  RAnal --> SvcAn
  RCase --> SvcCase
  RFeed --> SvcFeed
  RVault --> SvcVault
  RComm --> SvcComm
  SvcAuth & SvcWF & SvcAI & SvcAn & SvcCase & SvcFeed & SvcVault & SvcComm --> Repo
  Repo --> DB
```

---

## 4. C4 Level 4 — Identity component (Phase 6 focus)

```mermaid
flowchart LR
  Login[Login entry] --> Local[Local password verifier]
  Login --> OIDC[OIDC code exchange]
  Login --> SAML[SAML ACS]
  Login --> LDAP[LDAP/AD bind]
  Local --> Policy[Password policy]
  Local --> MFA[TOTP challenge]
  OIDC --> Session[Session service]
  SAML --> Session
  LDAP --> Session
  MFA --> Session
  Session --> Tokens[Access + Refresh JWT]
  Session --> Devices[Trusted devices]
  Admin[User admin API] --> Users[(users)]
  Admin --> Audit[(audit_logs)]
  Tokens --> RBAC[Permission check]
```

**Justification:** Complete the existing OIDC scaffold and MFA rather than replacing JWT. SAML/LDAP adapters feed the same session service so RBAC remains one place (`rbac.py` + `deps.py`).

---

## 5. Database ER (logical target)

```mermaid
erDiagram
  TENANTS ||--o{ USERS : has
  TENANTS ||--o{ INSTITUTIONS : has
  USERS ||--o{ SESSIONS : opens
  USERS ||--o{ TRUSTED_DEVICES : owns
  USERS ||--o{ AUDIT_LOGS : generates
  USERS ||--o{ INCIDENTS : reports
  INCIDENTS ||--o{ INCIDENT_EVENTS : timeline
  INCIDENTS ||--o{ CASES : may_open
  CASES ||--o{ CASE_NOTES : has
  CASES ||--o{ CASE_ASSIGNMENTS : has
  CASES ||--o{ EVIDENCE_ITEMS : links
  EVIDENCE_ITEMS ||--o{ EVIDENCE_CUSTODY : chain
  VERIFICATION_CHECKS ||--o{ EVIDENCE_ITEMS : may_become
  INSTITUTIONS ||--o{ OFFICIAL_HANDLES : has
  INSTITUTIONS ||--o{ ANNOUNCEMENTS : publishes
  ANNOUNCEMENTS ||--o{ ANNOUNCEMENT_VERSIONS : versions
  PARTNER_API_KEYS }o--|| INSTITUTIONS : optional
  INTEL_SOURCES ||--o{ INTEL_ITEMS : collects
  INTEL_ITEMS }o--o{ INCIDENTS : correlates
  MODEL_REGISTRY ||--o{ MODEL_EVALUATIONS : evaluated
```

**v0.9 reused entities:** users, institutions, official handles, verification_checks, incidents, audit, partner keys, MFA fields.  
**Additive only:** tenants, sessions, devices, cases, evidence_*, announcements, intel_*, model_*.

---

## 6. Service dependency diagram

```mermaid
flowchart BT
  platform --> text_check & impersonation & media_check & audio_check & ambassadors
  intelligence --> engines --> trust_fusion
  government --> incident_workflow
  analytics --> repositories
  identity --> security & rbac
  cases --> incident_workflow & vault
  feeds --> connectors --> correlation
  vault --> hashing & object_store
  communications --> crypto_sign & vault
  governance --> model_cards & risk_register
```

---

## 7. API dependency diagram

```mermaid
flowchart LR
  UI[Consoles] --> AuthAPI[/auth/*]
  UI --> PlatAPI[/check /analyze /incidents]
  UI --> GovAPI[/analyst /workflow]
  UI --> AnalAPI[/analytics/*]
  UI --> IntelAPI[/intelligence/*]
  UI --> CaseAPI[/cases/*]
  UI --> VaultAPI[/evidence/*]
  UI --> InstAPI[/institutions-admin/*]
  UI --> CommAPI[/announcements/*]
  Partners[Partners] --> KeyAuth[X-API-Key] --> PlatAPI & IntelAPI
  AuthAPI --> IdP[External IdP]
  VaultAPI --> S3[Object storage]
  CaseAPI --> GovAPI
  CommAPI --> VaultAPI
```

**Compatibility rule:** Existing paths keep verbs and schemas; new fields are optional; new resources get new prefixes.

---

## 8. AI pipeline diagram

```mermaid
flowchart TD
  Input[Text / media / identity / URLs] --> Normalize[Normalize + validate]
  Normalize --> Router[Engine router]
  Router --> E1[text]
  Router --> E2[image]
  Router --> E3[audio]
  Router --> E4[video]
  Router --> E5[identity]
  Router --> E6[document]
  Router --> E7[network]
  Router --> E8[source]
  Router --> E9[behavior]
  Router --> E10[metadata]
  E1 & E2 & E3 & E4 & E5 & E6 & E7 & E8 & E9 & E10 --> Fusion[Trust fusion]
  Fusion --> Explain[Explanations + band]
  Explain --> Persist[verification_checks]
  Explain --> Optional[Optional case / evidence link]
  Feedback[Analyst feedback] --> Eval[Evaluation store - Phase 12]
  Registry[Model registry] -.-> E1 & E2 & E3 & E4 & E6
```

Policy: unsupported engines return explicit scaffold status; fusion never invents certainty.

---

## 9. Identity flow diagram

```mermaid
sequenceDiagram
  actor U as User
  participant UI as Identity UI
  participant API as /api/v1/auth
  participant IdP as OIDC IdP
  participant DB as Database
  U->>UI: Choose local or SSO
  alt Local password
    UI->>API: POST /login
    API->>DB: Verify + lockout policy
    alt MFA enabled
      API-->>UI: mfa_required + mfa_token
      UI->>API: POST /mfa/verify
    end
    API-->>UI: access + refresh
  else OIDC
    UI->>API: GET /oidc/{id}/authorize
    API-->>UI: redirect URL
    UI->>IdP: Authorize
    IdP->>API: callback code
    API->>IdP: Token exchange
    API->>DB: Upsert user by oidc_subject
    API-->>UI: access + refresh
  end
  UI->>API: API calls with Bearer
```

SAML/LDAP follow the same post-auth session issuance.

---

## 10. Incident workflow diagram

```mermaid
stateDiagram-v2
  [*] --> open
  open --> ai_analysis
  open --> analyst_review
  open --> dismissed
  ai_analysis --> analyst_review
  ai_analysis --> dismissed
  analyst_review --> institution_review
  analyst_review --> decision
  analyst_review --> dismissed
  institution_review --> decision
  institution_review --> dismissed
  decision --> public_advisory
  decision --> resolved
  decision --> dismissed
  public_advisory --> resolved
  resolved --> archived
  dismissed --> archived
  archived --> [*]
```

**Phase 7 extension:** Cases attach to incidents without replacing this machine; case states are orthogonal (intake, investigating, pending_institution, closed).

---

## 11. Evidence management workflow

```mermaid
sequenceDiagram
  participant A as Analyst
  participant API as Evidence API
  participant V as Vault service
  participant S3 as Object store
  participant DB as DB
  A->>API: Register evidence (file or check id)
  API->>V: Compute hash (SHA-256+)
  V->>S3: Store blob
  V->>DB: evidence_items + custody genesis
  A->>API: Transfer custody
  API->>DB: Append custody event (who, why, hash verify)
  A->>API: Export package
  API->>V: Signed manifest + files
  V-->>A: Evidence export bundle
```

---

## 12. Deployment diagram (target national)

```mermaid
flowchart TB
  subgraph Edge
    WAF[WAF / TLS terminate]
  end
  subgraph Cluster["Kubernetes namespace mboashield"]
    ING[Ingress]
    API[API pods]
    WRK[Worker pods]
    RED[Redis]
  end
  PG[(Managed PostgreSQL)]
  MQ[RabbitMQ]
  OBJ[Object storage]
  MON[Prometheus Grafana Loki]
  WAF --> ING --> API
  API --> PG & RED & MQ & OBJ
  WRK --> PG & MQ & OBJ
  API --> MON
  WRK --> MON
```

**Demo profile retained:** single Docker web service on Render.

---

## 13. Network architecture

- Public zone: citizen UI, public verify URLs, health  
- Auth zone: IdP callbacks restricted by path  
- Operations zone: NTOC / admin (IP allowlists or VPN optional via config)  
- Partner zone: API keys + mTLS optional later  
- Data zone: Postgres, Redis, object store — private subnets  
- Egress allowlist for intel connectors (Phase 8)

---

## 14. Security architecture

| Layer | Controls |
|---|---|
| Edge | TLS 1.2+, HSTS, WAF rules |
| App | AUTH_ENFORCE profiles, RBAC, MFA, session revoke |
| Data | Encryption at rest, field encryption for secrets, hashed API keys |
| Evidence | Hash integrity, custody log, signed export |
| AI | Input size limits, no tool-execution from untrusted text, model allowlist |
| Ops | Audit logs immutable append, SIEM export |
| Supply chain | Pinned deps, CI tests, image scan (Phase 13) |

---

## 15. Trust score pipeline

```mermaid
flowchart LR
  Risks[Engine risk scores] --> Max[0.65 * max]
  Risks --> WAvg[0.35 * confidence-weighted avg]
  Max --> Fuse[fused_risk]
  WAvg --> Fuse
  Fuse --> Trust["trust = 100 - fused_risk"]
  Trust --> Band[high / medium / low]
  Trust --> Explain[Per-engine rationale]
  Band --> Policy[Never claim certainty]
```

Phase 12 may add calibrated probabilities **as separate fields** without removing heuristic trust.

---

## 16. Government operations workflow

1. Signal in (citizen report, partner API, intel feed)  
2. Incident opened ? AI analysis  
3. Analyst triage (NTOC) ? case assignment  
4. Evidence capture ? institution review if needed  
5. Decision ? public advisory and/or verified announcement  
6. Resolve ? archive ? retention policy  

---

## 17. Journey maps

### Citizen

Discover ? check claim/media ? optional report incident ? track status ? learn (Ambassadors) ? verify official announcement QR.

### Analyst

Login (MFA/SSO) ? national threat level ? queue ? open investigation workspace ? notes/evidence ? transition incident ? feedback labels ? close case.

### Institution administrator

SSO ? manage domains/handles ? review assigned incidents ? publish signed announcement ? view org analytics ? rotate API keys.

### Partner API

Obtain key ? `GET /partners/me` ? create checks / submit incidents per scopes ? consume webhooks (Phase 7+) ? rotate key.

---

## 18. Multi-country configuration model

```yaml
# Conceptual — implemented Phase 6+ as env + DB tenant profile
tenant:
  id: cm
  display_name: Cameroon
  languages: [en, fr]
  regions: [Adamawa, Centre, ...]
  idp: { type: oidc, issuer: ..., client_id: ... }
  branding: { app_name: MboaShield, primary_color: "..." }
  policies:
    auth_enforce: true
    mfa_required_roles: [admin, analyst]
    retention_days: 2555
    threat_level_thresholds: { elevated: 40, high: 70, critical: 85 }
  intel_egress_allowlist: ["https://rss.official.gov.cm/", "https://api..."]
```

Code paths read tenant context; no country forks.

---

## 19. UX principles (Principal UX)

- One job per console section; NTOC is operational, not marketing  
- Preserve Grand Jury demo as a **demo profile skin**, not the ops default  
- Progressive enhancement on existing HTML; optional later SPA only if needed  
- Accessibility: keyboard paths, contrast, language toggle EN/FR  
- Never show fake certainty badges on AI output  

---

## 20. Design decisions log

| Decision | Choice | Justification |
|---|---|---|
| Evolve monolith first | Yes | Avoid rewrite; seams already exist |
| Keep `/api/v1` | Yes | Non-breaking mandate |
| Soft auth demo profile | Retain | Competition + civic access |
| Cases vs incidents | Parallel models | Don’t break workflow machine |
| Intel compliance | Official APIs/RSS only | Legal & adoption fitness |
| Evidence additive | New tables | Don’t overload verification_checks |
| AI certainty | Remain none by default | Governance honesty |

**Next:** [`V1_0_THREAT_MODEL.md`](V1_0_THREAT_MODEL.md)
