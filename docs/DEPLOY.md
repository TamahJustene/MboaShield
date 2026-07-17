# Deploy MboaShield (public demo URL)

Use these for your **ictinnovationweek.cm** form demo link.

**Recommended:** Render hosts the full app (API + uploads + demo). Vercel is optional for a fast global frontend URL that talks to Render.

---

## Step 0 � Push code (done if you see this on GitHub)

```bash
cd mboashield
git push origin main
```

Repo: https://github.com/TamahJustene/MboaShield

---

## Option A � Render (recommended, full app)

Render runs the whole FastAPI server in Docker. This is your **primary competition URL**.

### Deploy (first time)

1. Open https://dashboard.render.com and sign in with **GitHub**
2. Click **New +** ? **Blueprint**
3. Connect repository: **TamahJustene/MboaShield**
4. Render reads `render.yaml` automatically � click **Apply**
5. Wait 3�8 minutes for the first build (free tier can be slow)
6. Copy your URL, e.g. `https://mboashield.onrender.com`

### Verify

Open in browser:

- `https://YOUR-URL.onrender.com/health` ? JSON with `"status":"ok"`
- `https://YOUR-URL.onrender.com` ? full demo UI
- `https://YOUR-URL.onrender.com/static/pitch.html` ? pitch deck

### Free tier notes

- Service **sleeps after ~15 min** of no traffic � first visit may take 30�60s to wake up
- Before the pitch, open the URL once to wake it, or click **Run 5-scenario pitch demo**
- Region is set to **Frankfurt** (closest EU region to Cameroon)

### Update Vercel proxy (if you use Vercel too)

After Render deploy, edit `vercel.json` and replace `mboashield.onrender.com` with your real Render hostname, then push.

### Put in competition form

```
https://YOUR-URL.onrender.com
```

---

## Option B � Vercel (frontend + API proxy to Render)

Vercel serves the UI globally; API calls are proxied to your Render backend.

**Deploy Render first** � Vercel needs a live Render URL in `vercel.json`.

### Deploy (first time)

1. Open https://vercel.com and sign in with **GitHub**
2. Click **Add New�** ? **Project**
3. Import **TamahJustene/MboaShield**
4. Framework Preset: **Other** (no build step)
5. Root Directory: leave as **.** (repo root � `vercel.json` sets `outputDirectory`)
6. Click **Deploy**
7. Copy URL, e.g. `https://mboashield.vercel.app`

### Verify

- `https://YOUR-URL.vercel.app` ? demo UI
- `https://YOUR-URL.vercel.app/health` ? proxied to Render
- Run **5-scenario pitch demo** � confirms API proxy works

### Limitations

- File uploads go through Vercel proxy (max ~4.5 MB on free tier)
- If Render is sleeping, Vercel UI loads but API may be slow on first request
- For Grand Jury live demo, prefer **Render URL directly**

---

## Option C � Instant tunnel (testing only)

```bash
cd mboashield
./scripts/public_tunnel.sh
```

Copy the `https://....trycloudflare.com` URL. URL changes every run � not for final submission.

---

## Option D � Local backup (pitch day)

```bash
./scripts/run_demo.sh
# http://127.0.0.1:8000
```

Record a 90s backup video on your phone.

---

## Which URL to submit?

| Platform | Use for |
|---|---|
| **Render** | Competition form, live pitch, full demo |
| **Vercel** | Extra link, sharing deck/UI quickly |
| **Tunnel** | Quick tests only |
| **Local** | Backup if venue Wi?Fi fails |

---

## Health check

```
GET /health
? {"status":"ok","version":"1.0.0","database":"sqlite|postgresql","auth_enforce":false,...}
```

Access modes, roles, and how to lock the API: [`ACCESS_AND_CONFIG.md`](ACCESS_AND_CONFIG.md).

---

## Production-like local stack (Phase 1)

```bash
cd mboashield
cp .env.example .env   # set JWT_SECRET
docker compose up --build
# API: http://127.0.0.1:8000
# Postgres: localhost:5432 (user/pass/db: mboashield)
```

SQLite remains the default for `./scripts/run_demo.sh` when `DATABASE_URL` is unset.

### Important env vars

Full adjustment guide: [`ACCESS_AND_CONFIG.md`](ACCESS_AND_CONFIG.md).

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL URL (`postgresql+psycopg://...`) |
| `MBOASHIELD_DB_PATH` | SQLite file path when not using Postgres |
| `JWT_SECRET` | Required strong secret in production |
| `AUTH_ENFORCE` | `true` to require JWT + RBAC on gated routes (live demo uses `false`) |
| `DEPLOYMENT_PROFILE` | `demo` or `government` (security warning profile) |
| `MFA_ENFORCE` | Require MFA enrollment for `MFA_REQUIRED_ROLES` before login completes |
| `MFA_REQUIRED_ROLES` | Roles recommended/required for MFA (default `admin`) |
| `OIDC_*` / `SAML_*` / `LDAP_*` | Federation providers (see `.env.example`) |
| `PASSWORD_RESET_RETURN_TOKEN` | Demo-only: return reset token in API body |
| `CORS_ORIGINS` | Comma-separated origins |
| `RATE_LIMIT_PER_MINUTE` | Per-client path rate limit |
| `MBOASHIELD_ENV` | `production` enables security warnings in logs |

### Migrations

```bash
# With DATABASE_URL set:
alembic upgrade head
```

On first boot the app also runs `create_all` so demo environments stay zero-friction.

---

## After deploy

1. Update `FORM_ANSWERS.md` with your live Render URL
2. Update `vercel.json` with the same Render hostname if using Vercel
3. Test the 5-scenario demo on mobile data (not just Wi-Fi)
4. For government deployments: attach managed Postgres, set `JWT_SECRET`, set `AUTH_ENFORCE=true`

---

## Government stack (Phase 13)

Demo compose (`docker-compose.yml`) is unchanged. For enterprise infra:

```bash
docker compose -f docker-compose.gov.yml up --build
```

Includes Postgres, Redis, RabbitMQ, API, Celery worker/beat, Prometheus (`:9090`), Grafana (`:3000`, admin/`mboashield`), Loki.

Kubernetes: `helm upgrade --install mboashield deploy/helm/mboashield`

See [`PHASE_13_PLAN.md`](PHASE_13_PLAN.md).
