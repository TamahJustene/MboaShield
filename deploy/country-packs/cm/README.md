# Cameroon country pack (MboaShield 2030 T0)

**Pack id:** `cm`  
**Env:** `COUNTRY_PACK=cm` (default)

## Purpose

Template for deploying MboaShield as **national digital trust infrastructure** in Cameroon without code changes. Other countries copy `deploy/country-packs/template/` and adjust.

## Configuration

| Variable | Cameroon default |
|---|---|
| `COUNTRY_PACK` | `cm` |
| `TENANT_ID` | `cm` |
| `TENANT_DISPLAY_NAME` | Cameroon |
| `DEPLOYMENT_PROFILE` | `demo` or `government` |

## Seeded data

- Institution registry: `data/institutions.json` (17 national institutions)
- Lessons: `data/lessons.json`
- AI golden sets: `data/ai_golden_en.json`, `data/ai_golden_fr.json`

## Legal / operational (operator responsibility)

- Data protection authority alignment (operator DPIA)
- National IdP integration via OIDC/SAML env vars
- CERT / ministry operating procedures

## Verify pack at runtime

```bash
curl -s http://127.0.0.1:8000/api/v1/program | python3 -m json.tool
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
```

Expect `"country_pack": "cm"`, `"program": "mboashield-2030"`.
