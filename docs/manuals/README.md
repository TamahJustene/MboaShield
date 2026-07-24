# MboaShield documentation suite (Phase 15)

**Product version:** 1.9.0  
**Audience:** external audit, operators, developers, and end users.

These manuals consolidate living source docs (Architecture, Access, Deploy, Threat Model, Phase plans) into role-oriented guides.

| Manual | Audience |
|---|---|
| [USER.md](USER.md) | Citizens and first-time demo users |
| [ADMINISTRATOR.md](ADMINISTRATOR.md) | Platform admins and institution operators |
| [DEVELOPER.md](DEVELOPER.md) | Engineers extending `/api/v1` |
| [OPERATIONS.md](OPERATIONS.md) | On-call / NTOC operators |
| [SECURITY.md](SECURITY.md) | Security reviewers |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deploy engineers |
| [MAINTENANCE.md](MAINTENANCE.md) | Backup, upgrades, retention |
| [API_REFERENCE.md](API_REFERENCE.md) | Integrators (beyond raw OpenAPI) |
| [ARCHITECTURE_GUIDE.md](ARCHITECTURE_GUIDE.md) | Architects and auditors |
| [AI_GOVERNANCE.md](AI_GOVERNANCE.md) | AI governance / compliance |

## Generated artifacts

```bash
# From mboashield/ repo root, with PYTHONPATH=.
python scripts/export_openapi.py
```

Writes:

- `docs/manuals/openapi.json` - machine-readable OpenAPI 3 export
- `docs/manuals/openapi.summary.md` - path inventory for quick review

Live interactive docs: `/docs` and `/redoc` on a running instance.

## Source of truth map

| Topic | Living doc |
|---|---|
| Product status | [`../PRODUCT_STATUS.md`](../PRODUCT_STATUS.md) |
| Access / env | [`../ACCESS_AND_CONFIG.md`](../ACCESS_AND_CONFIG.md) |
| Architecture | [`../ARCHITECTURE.md`](../ARCHITECTURE.md) |
| Deploy | [`../DEPLOY.md`](../DEPLOY.md) |
| Threat model | [`../V1_0_THREAT_MODEL.md`](../V1_0_THREAT_MODEL.md) |
| Enterprise index | [`../V1_0_ENTERPRISE_INDEX.md`](../V1_0_ENTERPRISE_INDEX.md) |
| Changelog | [`../../CHANGELOG.md`](../../CHANGELOG.md) |
