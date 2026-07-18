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

function getDeviceToken() {
  return localStorage.getItem("mboashield_device_token");
}

function setDeviceToken(token) {
  if (token) localStorage.setItem("mboashield_device_token", token);
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
    <p>Profile: <strong>${escapeHtml(data.deployment_profile)}</strong>  -  ENV: <strong>${escapeHtml(data.environment)}</strong>  -  AUTH_ENFORCE: <strong>${escapeHtml(data.auth_enforce)}</strong></p>
    <p>MFA enforce: <strong>${escapeHtml(data.mfa_enforce)}</strong>  -  OIDC: <strong>${escapeHtml(data.oidc_ready)}</strong>  -  SAML: <strong>${escapeHtml(data.saml_ready)}</strong>  -  LDAP: <strong>${escapeHtml(data.ldap_ready)}</strong></p>
    <p>Sessions / devices / admin users / password recovery: ready</p>
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
          <p class="history-item-title">${escapeHtml(key.partner_org)}  -  ${escapeHtml(key.key_prefix)}...</p>
          <p class="muted">${escapeHtml((key.scopes || []).join(", "))}</p>
        </article>
      `
    )
    .join("") || "<p class='muted'>No partner API keys yet.</p>";
}

async function loadSessions() {
  const list = document.getElementById("sessionList");
  const res = await fetch("/api/v1/auth/sessions", { headers: authHeaders() });
  if (!res.ok) {
    list.innerHTML = "<p class='muted'>Sign in to view sessions.</p>";
    return;
  }
  const data = await res.json();
  list.innerHTML = (data.sessions || [])
    .map(
      (item) => `
      <article class="history-item">
        <div class="history-item-top">
          <strong>${escapeHtml(item.auth_method)}</strong>
          <button type="button" class="btn-ghost" data-session="${escapeHtml(item.id)}">Revoke</button>
        </div>
        <p class="muted">${escapeHtml(item.created_at)}  -  ${escapeHtml(item.ip_address || "no-ip")}</p>
      </article>`
    )
    .join("") || "<p class='muted'>No active sessions.</p>";
  list.querySelectorAll("[data-session]").forEach((btn) => {
    btn.onclick = async () => {
      await fetch("/api/v1/auth/sessions/revoke", {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ session_id: btn.getAttribute("data-session") }),
      });
      loadSessions();
    };
  });
}

async function loadDevices() {
  const list = document.getElementById("deviceList");
  const res = await fetch("/api/v1/auth/devices", { headers: authHeaders() });
  if (!res.ok) {
    list.innerHTML = "<p class='muted'>Sign in to view trusted devices.</p>";
    return;
  }
  const data = await res.json();
  list.innerHTML = (data.devices || [])
    .map(
      (item) => `
      <article class="history-item">
        <div class="history-item-top">
          <strong>${escapeHtml(item.name)}</strong>
          <button type="button" class="btn-ghost" data-device="${item.id}">Revoke</button>
        </div>
        <p class="muted">Expires ${escapeHtml(item.expires_at)}</p>
      </article>`
    )
    .join("") || "<p class='muted'>No trusted devices.</p>";
  list.querySelectorAll("[data-device]").forEach((btn) => {
    btn.onclick = async () => {
      await fetch(`/api/v1/auth/devices/${btn.getAttribute("data-device")}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      loadDevices();
    };
  });
}

async function loadUsers() {
  const list = document.getElementById("userList");
  const res = await fetch("/api/v1/admin/users", { headers: authHeaders() });
  if (!res.ok) {
    list.innerHTML = "<p class='muted'>Admin list unavailable (need users:manage when enforced).</p>";
    return;
  }
  const data = await res.json();
  list.innerHTML = (data.users || [])
    .map(
      (user) => `
      <article class="history-item">
        <div class="history-item-top">
          <strong>${escapeHtml(user.display_name)}</strong>
          <span class="band low">${escapeHtml(user.role)}</span>
        </div>
        <p class="muted">${escapeHtml(user.email || "")}  -  active=${escapeHtml(user.is_active)}</p>
      </article>`
    )
    .join("") || "<p class='muted'>No users.</p>";
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
      device_token: getDeviceToken(),
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
  loadSessions();
  loadDevices();
  loadUsers();
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
      trust_device: document.getElementById("trustDevice").checked,
      device_name: "Browser device",
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    status.textContent = data.error?.message || data.detail || "MFA failed";
    return;
  }
  setAccessToken(data.access_token);
  if (data.device_token) setDeviceToken(data.device_token);
  status.textContent = "MFA verified.";
  loadSessions();
  loadDevices();
});

document.getElementById("startOidc").onclick = async () => {
  const status = document.getElementById("ssoStatus");
  const providers = await fetch("/api/v1/auth/oidc/providers").then((r) => r.json());
  const provider = (providers.providers || [])[0];
  if (!provider) {
    status.textContent = "No OIDC provider configured. Set OIDC_ISSUER and OIDC_CLIENT_ID.";
    return;
  }
  const auth = await fetch(provider.authorize_path).then((r) => r.json());
  if (!auth.authorize_url) {
    status.textContent = auth.detail || "Could not start OIDC";
    return;
  }
  status.textContent = "Redirecting to IdP...";
  window.location.href = auth.authorize_url;
};

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

document.getElementById("forgotForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = document.getElementById("forgotStatus");
  const res = await fetch("/api/v1/auth/password/forgot", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: document.getElementById("forgotEmail").value.trim() }),
  });
  const data = await res.json();
  status.textContent = data.reset_token
    ? `Token (dev return): ${data.reset_token}`
    : data.message || "Request accepted";
  if (data.reset_token) document.getElementById("resetToken").value = data.reset_token;
});

document.getElementById("resetForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = document.getElementById("resetStatus");
  const res = await fetch("/api/v1/auth/password/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      token: document.getElementById("resetToken").value.trim(),
      new_password: document.getElementById("resetPassword").value,
    }),
  });
  const data = await res.json();
  status.textContent = res.ok ? "Password updated." : data.error?.message || data.detail || "Reset failed";
});

document.getElementById("adminUserForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = document.getElementById("adminUserStatus");
  const res = await fetch("/api/v1/admin/users", {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      display_name: document.getElementById("adminName").value.trim(),
      email: document.getElementById("adminEmail").value.trim(),
      role: document.getElementById("adminRole").value,
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    status.textContent = data.error?.message || data.detail || "Create failed";
    return;
  }
  status.textContent = `Created ${data.user.email}. Temp password: ${data.temporary_password}`;
  loadUsers();
});

document.getElementById("oauthClientForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = document.getElementById("oauthStatus");
  const res = await fetch("/api/v1/oauth/clients", {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      name: document.getElementById("oauthName").value.trim(),
      partner_org: document.getElementById("oauthOrg").value.trim(),
      scopes: ["checks:create", "institutions:read"],
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    status.textContent = data.error?.message || data.detail || "Create failed";
    return;
  }
  status.textContent = `client_id=${data.client_id} client_secret=${data.client_secret}`;
});

document.getElementById("loadSessions").onclick = loadSessions;
document.getElementById("loadDevices").onclick = loadDevices;
document.getElementById("loadUsers").onclick = loadUsers;
document.getElementById("revokeAllSessions").onclick = async () => {
  await fetch("/api/v1/auth/sessions/revoke", {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ revoke_all: true }),
  });
  loadSessions();
};

loadSecurityStatus();
loadApiKeys();
if (getAccessToken()) {
  loadSessions();
  loadDevices();
  loadUsers();
}
