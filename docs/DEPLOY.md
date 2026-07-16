# Deploy MboaShield (public demo URL)

Use one of these for your **ictinnovationweek.cm** form demo link.

---

## Option A — Render (recommended, free, stable URL)

1. Push latest code: `git push origin main`
2. Go to https://dashboard.render.com ? **New** ? **Blueprint**
3. Connect GitHub repo: `TamahJustene/MboaShield`
4. Render reads `render.yaml` automatically
5. Deploy ? copy URL, e.g. `https://mboashield.onrender.com`
6. Test: `https://YOUR-URL/health` should return JSON

**Put this URL in your competition form.**

---

## Option B — Instant tunnel (5 minutes, temporary URL)

```bash
cd mboashield
chmod +x scripts/public_tunnel.sh
./scripts/public_tunnel.sh
```

Copy the `https://....trycloudflare.com` URL shown. Good for testing; URL changes each run.

Install cloudflared:
```bash
# Ubuntu/Debian
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cf.deb
sudo dpkg -i /tmp/cf.deb
```

---

## Option C — Docker anywhere

```bash
docker build -t mboashield .
docker run -p 8000:8000 mboashield
```

---

## Option D — Local only (pitch backup)

```bash
./scripts/run_demo.sh
# Open http://127.0.0.1:8000
# Also record 90s backup video on phone
```

---

## Health check

```
GET /health
? {"status":"ok","version":"0.2.0","founder":"Justene Nkwagoh Tamah","product":"MboaShield"}
```

---

## After deploy

Update `FORM_ANSWERS.md` demo URL and re-submit if the form allows edits before 22 Jul 15:30.
