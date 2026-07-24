# MboaShield v1.0 - Threat Model

**Baseline:** v0.9.0 - **Design:** [`V1_0_SYSTEM_DESIGN.md`](V1_0_SYSTEM_DESIGN.md)  
**Method:** STRIDE + abuse/misuse + AI-specific risks - **Owner roles:** Principal Cybersecurity - AI Governance - DevSecOps - Digital Identity  

---

## 1. Assets to protect

| Asset | Sensitivity |
|---|---|
| Citizen PII (email, display name, optional contact) | High |
| Credentials, MFA secrets, refresh tokens, API keys | Critical |
| Incident / case content and analyst notes | Critical |
| Evidence blobs and custody logs | Critical |
| Institution registry and official handles | High |
| Signed government announcements | Critical |
| Audit logs | High (integrity) |
| Model weights / prompts / evaluation sets | High |
| National threat dashboards (availability) | High |

---

## 2. Attack surface analysis

| Surface | Exposure today | Notes |
|---|---|---|
| Public HTTP API `/api/v1/*` | Open (soft auth) | Primary surface |
| Static consoles | Public | No server-side page auth |
| File upload analyze | Public | Size/type abuse |
| OIDC callback | Partial | Incomplete exchange risk |
| Partner API keys | Create needs manage perm when enforced | Soft mode open |
| Render free tier | Public internet | Cold start / noisy neighbor |
| Dependencies (PyPI) | Supply chain | requirements.txt |
| Admin via SQL role edit | Operator error | Until Phase 6 UI |
| Future intel connectors | Egress | Must be allowlisted |
| Future object storage | Credentials | KMS/IAM |

---

## 3. STRIDE Threat Model

### Spoofing

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Stolen password | Med | High | MFA enforce for privileged roles (Phase 6); lockout; IdP |
| Stolen JWT | Med | High | Short TTL; refresh rotation; session revoke; device binding |
| Forged partner key | Low | High | Hash at rest; show once; scope least privilege |
| Fake institution handle in registry | Med | High | Dual control for institutions:manage; audit |
| Spoofed IdP | Low | Critical | Validate issuer, JWKS, state/nonce, audience |

### Tampering

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Alter incident status illegally | Med | High | Enforce AUTH + transition rules; audit |
| Tamper evidence file | Med | Critical | Hash + custody chain + immutable object versioning |
| Modify audit rows | Low | Critical | Append-only table / WORM storage (Phase 9/13) |
| Poison analytics feedback | Med | Med | Authenticated analysts only when enforced |

### Repudiation

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Analyst denies action | Med | High | Actor id/role on audit; case notes authorship |
| Partner denies API call | Med | Med | API key id in audit; request ids |
| Custody dispute | Med | Critical | Signed custody events |

### Information disclosure

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Soft auth exposes ops APIs | **High today** | High | Gov profile AUTH_ENFORCE=true; network allowlists |
| Verbose errors leak internals | Med | Med | Unified error sanitization |
| Cross-tenant data bleed | High if multi-tenant naive | Critical | tenant_id on all rows + query filters / RLS |
| Evidence export overbroad | Med | Critical | Role checks; watermarked exports; purpose codes |

### Denial of service

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Flood /analyze | High | High | Rate limits by IP + identity; async queue; quotas |
| Large media upload | High | High | Size/MIME caps; virus scan optional |
| Intel feed flood | Med | Med | Backpressure; per-source quotas |
| DB exhaustion | Med | High | Connection pools; statement timeouts |

### Elevation of privilege

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Citizen self-promotes role | Low (no API) | Critical | Only admin users:manage; dual control optional |
| API key scope creep | Med | High | Default minimal scopes; review UI |
| MFA bypass | Med | High | Challenge required when enabled; block tokens without amr |
| IDOR on incidents | Med | High | Ownership checks for citizens; role for analysts |
| Soft-mode -auth bypass- treated as feature in gov | High | Critical | Deployment profiles; startup refuse if prod+soft without override acknowledge |

---

## 4. Abuse cases (malicious intentional)

1. **Disinformation laundering:** Attacker mass-submits -clean- checks to skew analytics ? quotas, anomaly detection, analyst verification flags.  
2. **Registry poisoning:** Insert fake official accounts ? dual approval for institution changes.  
3. **Case flooding:** Open thousands of incidents ? rate limits + triage priorities.  
4. **Evidence planting:** Upload unrelated media into a case ? custody + hash + reviewer attestation.  
5. **Announcement forgery:** Fake -ministry- message ? cryptographic signatures + public verify URL (Phase 11).  
6. **Partner key theft:** Exfiltrate `msb_` key ? rotation, anomaly alerts, short-lived keys optional.  
7. **SSO account takeover:** Compromised IdP user ? MFA step-up for privileged actions.  

---

## 5. Misuse cases (unintentional / policy)

1. Analyst shares screen with PII in public pitch ? demo dataset mode.  
2. Admin leaves AUTH_ENFORCE=false on ministry network ? config lint + health exposes `auth_enforce`.  
3. Over-retention of citizen media ? retention jobs (Phase 9).  
4. Using heuristic -high risk- as legal proof ? UI + docs forbid certainty; governance training.  
5. Connecting scrapers that violate platform ToS ? **forbidden by policy**; Phase 8 connectors must declare license/ToS class.  

---

## 6. Privilege escalation analysis

```text
citizen
  -> (needs users:manage) analyst | institution_admin | admin

partner API key
  -> only mapped scopes (cannot become admin JWT)

OIDC linked account
  -> role from assertion mapped attributes OR local role table (never trust unverified claims alone)
```

**Control:** Role source of truth remains local `users.role` unless explicit attribute mapping policy is configured per tenant. IdP groups mapped via allowlist.

---

## 7. Data protection analysis

| Data class | At rest | In transit | Access |
|---|---|---|---|
| Passwords | Hash (existing) | TLS | Auth service only |
| MFA secrets | Encrypted/restricted column (harden Phase 6) | TLS | Auth only |
| API keys | SHA-256 hash | TLS | Shown once |
| Evidence | Object store encryption + app hash | TLS | Case roles |
| PII | DB encryption at rest (infra) | TLS | RBAC |
| Backups | Encrypted | Controlled | Ops runbooks |

---

## 8. Identity risks

| Risk | Mitigation phase |
|---|---|
| Incomplete OIDC callback | 6 - complete or disable |
| No password recovery | 6 |
| No session inventory | 6 |
| MFA only optional for admins | 6 - enforce for MFA_REQUIRED_ROLES |
| LDAP credential stuffing | 6 - lockout + IdP rate |
| SAML XML attacks | 6 - hardened library, entity allowlist |

---

## 9. Supply chain risks

- Unpinned transitive deps ? pin + `pip audit` / OSV in CI (Phase 13/14)  
- Base image drift ? digest-pinned Dockerfile  
- Malicious model download ? model registry checksums (Phase 12)  
- Typosquat packages ? review new deps in PR  

---

## 10. AI risks

| Risk | Description | Mitigation |
|---|---|---|
| Overconfidence | Users treat score as proof | `certainty: none`; UX copy; model cards |
| Bias | Language/region skew | Eval sets per language; human review |
| Drift | Engine changes alter outcomes | Version engines; changelog; shadow eval |
| Automation harm | Auto-public advisory from AI alone | Require human decision state |
| Secret leakage in logs | Prompt/input logged | Redact; retention |

---

## 11. Deepfake-specific risks

- False positive harms reputation ? human review gates before public advisory  
- False negative enables scam ? multi-engine fusion + institution verify channels  
- Adversarial perturbations ? ensemble + metadata/network signals; never single modality  
- Real-time voice scam ? audio engine + citizen UX urgency warnings (existing behavior path)  

---

## 12. Prompt injection risks

Even with heuristics, future LLM assists must assume **untrusted content**:

- Treat claim text / web page bodies as data, not instructions  
- No agent tools with destructive power on raw internet text  
- Separate system policy channel from user content  
- Sanitize content before analyst display (linkification caution)  

---

## 13. Model poisoning risks

- Attacker submits feedback to shift thresholds ? authenticated feedback + anomaly review  
- Compromised training data in Phase 12 ? dataset cards, provenance, checksums  
- Supply-chain model swap ? registry digests + signature  

---

## 14. Business continuity risks

| Risk | Impact | Mitigation |
|---|---|---|
| Render sleep during national event | Availability | Reserved capacity profile (Phase 13) |
| SQLite loss on restart | Data loss | Postgres required for gov profile |
| Single region outage | Outage | Backup region + DR plan |
| Key person dependency | Ops failure | Runbooks Phase 15; dual admin |

---

## 15. Disaster recovery assessment

| Item | RPO target (gov) | RTO target (gov) | Mechanism |
|---|---|---|---|
| Database | ? 15 min | ? 1 h | Managed PITR backups |
| Object evidence | ? 15 min | ? 2 h | Cross-region replication |
| Config/secrets | ? 24 h | ? 1 h | Infra-as-code + secret manager |
| App deploy | n/a | ? 30 min | Helm rollback / prior image |

Demo profile: best-effort; no national RPO claim.

---

## 16. Mitigation plan (prioritized)

### P0 - Before any ministry hard launch

1. `AUTH_ENFORCE=true` + Postgres + strong `JWT_SECRET` + narrow CORS  
2. Complete or disable OIDC stub  
3. Admin user management API + MFA mandatory for admin/analyst  
4. Gate remaining sensitive routes; keep public check endpoints deliberately public only if product policy says so  
5. Backup/restore drill documented  

### P1 - Phase 7-9

6. Case/evidence custody  
7. Notification integrity  
8. Retention & export controls  
9. Network allowlists for NTOC  

### P2 - Phase 12-14

10. Model registry integrity  
11. Prompt-injection hardened LLM assists (if introduced)  
12. SBOM + vulnerability SLAs  
13. Compliance dashboards  

### Continuous

14. Threat model review each phase exit  
15. Penetration test before national go-live  
16. Red-team abuse cases annually  

---

## 17. Phase 8 compliance note (mandatory)

Threat intelligence connectors **must** implement only:

- Official platform APIs with valid credentials and ToS-compliant use  
- RSS/Atom and other explicitly public feeds  
- Government open-data portals and licensed datasets  
- Partner-provided push APIs / webhooks  

**Out of scope / forbidden:** credential stuffing, bypassing access controls, undocumented scraping of Facebook, X, YouTube, Telegram, or similar services.

Each connector carries metadata: `source_class`, `tos_reference`, `license`, `egress_host`.

---

## 18. Residual risk statement

After Phases 6-9 and P0 mitigations, residual risk remains in AI false positives/negatives and nation-state adversaries. Residual risk is accepted only with human-in-the-loop decisions, honest uncertainty, and continuous evaluation - never with automated legal determinations.

**Next:** [`V1_0_IMPLEMENTATION_ROADMAP.md`](V1_0_IMPLEMENTATION_ROADMAP.md)
