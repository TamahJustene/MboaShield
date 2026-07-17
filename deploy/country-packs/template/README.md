# Country pack template

Copy this directory to `deploy/country-packs/{iso}/` and edit:

1. `pack.json` — pack_id, name, locales
2. `README.md` — legal and IdP notes
3. Seed `data/institutions.json` for that country (or override path via future config)

Set environment:

```bash
COUNTRY_PACK=xx
TENANT_ID=xx
TENANT_DISPLAY_NAME="Country Name"
```

No application code changes required for T0/T7 baseline.
