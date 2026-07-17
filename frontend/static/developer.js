function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function authHeaders(extra = {}) {
  if (window.MboaShieldPortal) return window.MboaShieldPortal.authHeaders(extra);
  const token = localStorage.getItem("mboashield_access_token");
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
}

async function loadProgram() {
  const lead = document.getElementById("devProgramLead");
  try {
    const data = await fetch("/api/v1/program").then((r) => r.json());
    lead.textContent = `${data.program} · ${data.version} · phase ${data.transformation_phase} · tenant ${data.tenant_display_name || data.tenant_id}`;
  } catch (_) {
    lead.textContent = "Could not load /api/v1/program";
  }
}

async function loadKeys() {
  const list = document.getElementById("devKeyList");
  const res = await fetch("/api/v1/partners/keys", { headers: authHeaders() });
  if (!res.ok) {
    list.innerHTML =
      "<p class='muted'>Sign in as admin (Identity) to list partner keys when AUTH_ENFORCE is on. Soft-auth demo may still list keys.</p>";
    return;
  }
  const keys = await res.json();
  const items = Array.isArray(keys) ? keys : keys.keys || [];
  list.innerHTML =
    items
      .map(
        (key) => `
      <article class="history-item">
        <div class="history-item-top">
          <strong>${escapeHtml(key.name)}</strong>
          <span class="band ${key.revoked ? "high" : "low"}">${key.revoked ? "REVOKED" : "ACTIVE"}</span>
        </div>
        <p class="muted">${escapeHtml(key.partner_org || "")} · ${escapeHtml(key.key_prefix || "")}...</p>
      </article>`
      )
      .join("") || "<p class='muted'>No partner API keys yet. Create one on Identity.</p>";
}

function renderSnippet() {
  document.getElementById("devSnippet").textContent = `curl -s -X POST "$BASE/api/v1/trust/assess" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer $TOKEN" \\
  -d '{"object_type":"text","text":"Urgent mobile money request","lang":"en"}'`;
}

loadProgram();
loadKeys();
renderSnippet();
