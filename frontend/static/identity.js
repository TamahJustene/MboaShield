function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function getAccessToken() {
  return localStorage.getItem("mboashield_access_token");
}

function setAccessToken(token) {
  if (token) localStorage.setItem("mboashield_access_token", token);
}

function authHeaders(extra = {}) {
  const token = getAccessToken();
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
}

let mfaToken = null;

async function loadSecurityStatus() {
  const res = await fetch("/api/v1/auth/security-status");
  const data = await res.json();
  document.getElementById("securityStatus").innerHTML = `
    <p>Environment: <strong>${escapeHtml(data.environment)}</strong> · AUTH_ENFORCE: <strong>${escapeHtml(data.auth_enforce)}</strong></p>
    <p>MFA ready: <strong>${escapeHtml(data.mfa_ready)}</strong> · OIDC ready: <strong>${escapeHtml(data.oidc_ready)}</strong> · Partner keys: <strong>${escapeHtml(data.partner_api_keys_ready)}</strong></p>
    <p>OIDC providers: <strong>${escapeHtml(data.oidc_providers?.length ?? 0)}</strong></p>
    <p class="muted">Warnings: ${escapeHtml((data.warnings || []).join("; ") || "none")}</p>
  `;
}

async function loadApiKeys() {
  const res = await fetch("/api/v1/partners/keys", { headers: authHeaders() });
  const list = document.getElementById("apiKeyList");
  if (!res.ok) {
    list.innerHTML = "<p class='muted'>Could not load API keys (admin permission may be required when AUTH_ENFORCE=true).</p>";
    return;
  }
  const keys = await res.json();
  list.innerHTML = (keys || [])
    .map(
      (key) => `
        <article class="history-item">
          <div class="history-item-top">
            <strong>${escapeHtml(key.name)}</strong>
            <span class="band ${key.revoked ? "high" : "low"}">${key.revoked ? "REVOKED" : "ACTIVE"}</span>
          </div>
          <p class="history-item-title">${escapeHtml(key.partner_org)} · ${escapeHtml(key.key_prefix)}...</p>
          <p class="muted">${escapeHtml((key.scopes || []).join(", "))}</p>
        </article>
      `
    )
    .join("") || "<p class='muted'>No partner API keys yet.</p>";
}

document.getElementById("loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = document.getElementById("loginStatus");
  status.textContent = "Signing in...";
  const res = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: document.getElementById("loginEmail").value.trim(),
      password: document.getElementById("loginPassword").value,
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    status.textContent = data.error?.message || data.detail || "Login failed";
    return;
  }
  if (data.mfa_required) {
    mfaToken = data.mfa_token;
    document.getElementById("mfaForm").classList.remove("hidden");
    status.textContent = "MFA required. Enter authenticator code.";
    return;
  }
  setAccessToken(data.access_token);
  status.textContent = `Signed in as ${data.user?.display_name || "user"}`;
});

document.getElementById("mfaForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = document.getElementById("mfaStatus");
  status.textContent = "Verifying MFA...";
  const res = await fetch("/api/v1/auth/mfa/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      code: document.getElementById("mfaCode").value.trim(),
      mfa_token: mfaToken,
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    status.textContent = data.error?.message || data.detail || "MFA failed";
    return;
  }
  setAccessToken(data.access_token);
  status.textContent = "MFA verified.";
});

document.getElementById("setupMfa").onclick = async () => {
  const out = document.getElementById("mfaSetupOut");
  const res = await fetch("/api/v1/auth/mfa/setup", { method: "POST", headers: authHeaders() });
  const data = await res.json();
  if (!res.ok) {
    out.className = "out history-detail is-ready";
    out.textContent = data.error?.message || data.detail || "MFA setup requires login.";
    return;
  }
  out.className = "out history-detail is-ready";
  out.textContent = `Secret: ${data.secret}\nURI: ${data.otpauth_uri}`;
};

document.getElementById("enableMfaForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = document.getElementById("enableMfaStatus");
  const res = await fetch("/api/v1/auth/mfa/enable", {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ code: document.getElementById("enableMfaCode").value.trim() }),
  });
  const data = await res.json();
  status.textContent = res.ok ? "MFA enabled." : data.error?.message || data.detail || "Enable failed";
});

document.getElementById("apiKeyForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = document.getElementById("apiKeyStatus");
  const scopes = document
    .getElementById("keyScopes")
    .value.split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  status.textContent = "Creating key...";
  const res = await fetch("/api/v1/partners/keys", {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      name: document.getElementById("keyName").value.trim(),
      partner_org: document.getElementById("keyOrg").value.trim(),
      scopes,
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    status.textContent = data.error?.message || data.detail || "Create failed";
    return;
  }
  status.textContent = `Created key (copy now): ${data.api_key}`;
  loadApiKeys();
});

loadSecurityStatus();
loadApiKeys();
