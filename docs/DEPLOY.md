# Deploy MboaShield

Public demo: https://mboashield.onrender.com

---

## Option A — Render (recommended, full app)

1. Open https://dashboard.render.com and sign in with GitHub
2. **New +** → **Blueprint**
3. Connect **TamahJustene/MboaShield**
4. Apply `render.yaml`
5. Wait for the first build, then copy the URL

### Verify

- `/health` → `"status":"ok"`
- `/` → citizen guided demo
- `/static/hub.html` → all product surfaces

### Free-tier notes

- Service may sleep after idle time; first request can take 30–60s
- Wake with `/health` before demos

---

## Option B — Local

```bash
cd mboashield
./scripts/run_demo.sh
# http://127.0.0.1:8000
```

---

## Option C — Tunnel (temporary)

```bash
./scripts/public_tunnel.sh
```

URL changes each run — testing only.

---

## Option D — Docker Compose

```bash
cp .env.example .env   # set JWT_SECRET
docker compose up --build
```

National / government target stack (requires injected secrets):

```bash
docker compose -f docker-compose.gov.yml up --build
```

Kubernetes: `helm upgrade --install mboashield deploy/helm/mboashield`

---

## Important env vars

Full guide: [`ACCESS_AND_CONFIG.md`](ACCESS_AND_CONFIG.md).

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres URL when not using SQLite |
| `JWT_SECRET` | Required strong secret outside demo |
| `AUTH_ENFORCE` | `true` for hard auth on gated routes |
| `DEPLOYMENT_PROFILE` | `demo` or `national` / `government` |
| `MFA_ENFORCE` | Require MFA for configured roles |
| `CORS_ORIGINS` | Explicit origins in national profile |
| `WEBHOOK_SIGNING_SECRET` / announcement / vault keys | Distinct signing secrets |

### Migrations

```bash
alembic upgrade head
```

Demo boot also runs `create_all` for zero-friction local use.

---

## After deploy

1. Confirm `/health` version and phase
2. Run guided demo once end-to-end
3. For national deployments: Postgres, hard auth, injected secrets, workers as needed
