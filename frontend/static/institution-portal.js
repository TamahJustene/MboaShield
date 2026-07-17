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

function errMessage(data) {
  return data?.error?.message || data?.detail || "Request failed";
}

let activeInstitutionId = null;

async function loadInstitutionOptions() {
  const res = await fetch("/api/v1/institutions");
  const data = await res.json();
  const list = document.getElementById("institutionOptions");
  list.innerHTML = (data.institutions || [])
    .map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.short_name)}</option>`)
    .join("");
}

async function refreshPortal() {
  if (!activeInstitutionId) return;
  const res = await fetch(`/api/v1/institution-portal/${encodeURIComponent(activeInstitutionId)}/overview`, {
    headers: authHeaders(),
  });
  const data = await res.json();
  const box = document.getElementById("overviewBox");
  if (!res.ok) {
    box.innerHTML = `<p class="report-copy">${escapeHtml(errMessage(data))}</p>`;
    return;
  }
  const inst = data.institution || {};
  const analytics = data.analytics || {};
  box.className = "out history-detail is-ready";
  box.innerHTML = `
    <h3>${escapeHtml(inst.short_name)} ù ${escapeHtml(inst.name)}</h3>
    <p class="muted">Members ${escapeHtml(data.active_members)} ù Verified domains ${escapeHtml(data.verified_domains)}</p>
    <p>Incidents open ${escapeHtml(analytics.incidents_open)} / ${escapeHtml(analytics.incidents_total)} ù Cases open ${escapeHtml(analytics.cases_open)} / ${escapeHtml(analytics.cases_total)}</p>
  `;

  const branding = (data.institution && data.institution.branding) || {};
  document.getElementById("brandColor").value = branding.primary_color || "";
  document.getElementById("brandLogo").value = branding.logo_url || "";
  document.getElementById("brandEmail").value = inst.contact_email || "";

  document.getElementById("domainList").innerHTML =
    (data.domains || [])
      .map(
        (item) => `
      <article class="history-item">
        <div class="history-item-top">
          <strong>${escapeHtml(item.domain)}</strong>
          <span class="band ${item.verified ? "low" : "medium"}">${item.verified ? "VERIFIED" : "PENDING"}</span>
        </div>
        <p class="muted">TXT ${escapeHtml(item.dns_txt_name)} = ${escapeHtml(item.dns_txt_value)}</p>
        ${
          item.verified
            ? ""
            : `<button type="button" class="btn-ghost" data-verify-domain="${item.id}" data-token="${escapeHtml(item.verification_token)}">Verify with token</button>`
        }
      </article>`
      )
      .join("") || "<p class='muted'>No domains yet.</p>";

  document.querySelectorAll("[data-verify-domain]").forEach((btn) => {
    btn.onclick = async () => {
      const domainId = btn.getAttribute("data-verify-domain");
      const token = btn.getAttribute("data-token");
      await fetch(
        `/api/v1/institution-portal/${encodeURIComponent(activeInstitutionId)}/domains/${domainId}/verify`,
        {
          method: "POST",
          headers: authHeaders({ "Content-Type": "application/json" }),
          body: JSON.stringify({ token }),
        }
      );
      refreshPortal();
    };
  });

  document.getElementById("memberList").innerHTML =
    (data.memberships || [])
      .map((item) => {
        const user = item.user || {};
        return `<p><strong>${escapeHtml(user.display_name || user.email || item.user_id)}</strong> ù ${escapeHtml(item.member_role)} ù ${escapeHtml(item.status)}</p>`;
      })
      .join("") || "<p class='muted'>No members yet.</p>";

  document.getElementById("accountList").innerHTML =
    (data.official_accounts || [])
      .map((item) => `<p>${escapeHtml(item.platform)} ${escapeHtml(item.handle)}</p>`)
      .join("") || "<p class='muted'>No official accounts yet.</p>";

  document.getElementById("keyList").innerHTML =
    (data.api_keys || [])
      .map((item) => `<p>${escapeHtml(item.name)} ù ${escapeHtml(item.key_prefix)}ù ù scopes ${(item.scopes || []).join(", ")}</p>`)
      .join("") || "<p class='muted'>No institution API keys yet.</p>";

  document.getElementById("caseList").innerHTML =
    ((await (await fetch(`/api/v1/institution-portal/${encodeURIComponent(activeInstitutionId)}/investigations`, { headers: authHeaders() })).json()).cases || [])
      .map((item) => `<p>#${item.id} ${escapeHtml(item.title)} ù ${escapeHtml(item.status)} ù ${escapeHtml(item.priority)}</p>`)
      .join("") || "<p class='muted'>No institution-scoped cases yet.</p>";

  await refreshTrustNetwork();
}

async function refreshTrustNetwork() {
  if (!activeInstitutionId) return;
  const relRes = await fetch(
    `/api/v1/trust-network/relationships?institution_id=${encodeURIComponent(activeInstitutionId)}`,
    { headers: authHeaders() }
  );
  const relData = await relRes.json();
  document.getElementById("partnerList").innerHTML =
    (relData.relationships || [])
      .map((item) => {
        const peer =
          item.source_institution_id === activeInstitutionId
            ? item.target_institution_id
            : item.source_institution_id;
        return `
      <article class="history-item">
        <div class="history-item-top">
          <strong>${escapeHtml(peer)}</strong>
          <span class="band ${item.status === "active" ? "low" : "medium"}">${escapeHtml(item.status)}</span>
        </div>
        <p class="muted">#${escapeHtml(item.id)} ù ${escapeHtml(item.policy_note || "no policy note")}</p>
        ${
          item.status === "pending"
            ? `<button type="button" class="btn-ghost" data-activate-rel="${item.id}">Activate</button>`
            : ""
        }
      </article>`;
      })
      .join("") || "<p class='muted'>No trust relationships yet.</p>";

  document.querySelectorAll("[data-activate-rel]").forEach((btn) => {
    btn.onclick = async () => {
      const id = btn.getAttribute("data-activate-rel");
      await fetch(`/api/v1/trust-network/relationships/${id}`, {
        method: "PATCH",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ status: "active" }),
      });
      refreshTrustNetwork();
    };
  });

  const alertRes = await fetch(
    `/api/v1/trust-network/exchange/alerts?institution_id=${encodeURIComponent(activeInstitutionId)}`,
    { headers: authHeaders() }
  );
  const alertData = await alertRes.json();
  document.getElementById("alertList").innerHTML =
    (alertData.alerts || [])
      .map(
        (item) => `
      <article class="history-item">
        <div class="history-item-top">
          <strong>${escapeHtml(item.alert_type)}</strong>
          <span class="band ${item.severity === "high" || item.severity === "critical" ? "high" : "medium"}">${escapeHtml(item.severity)}</span>
        </div>
        <p class="history-item-title">${escapeHtml(item.title)}</p>
        <p class="muted">from ${escapeHtml(item.source_institution_id)} ù #${escapeHtml(item.id)}</p>
      </article>`
      )
      .join("") || "<p class='muted'>No shared alerts in your inbox yet.</p>";
}

document.getElementById("selectForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  activeInstitutionId = document.getElementById("institutionId").value.trim().toLowerCase();
  document.getElementById("selectStatus").textContent = `Opened ${activeInstitutionId}`;
  await refreshPortal();
});

document.getElementById("domainForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!activeInstitutionId) return;
  const status = document.getElementById("domainStatus");
  const res = await fetch(`/api/v1/institution-portal/${encodeURIComponent(activeInstitutionId)}/domains`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      domain: document.getElementById("domainName").value.trim(),
      verification_method: document.getElementById("domainMethod").value,
    }),
  });
  const data = await res.json();
  status.textContent = res.ok ? `Added ${data.domain}` : errMessage(data);
  if (res.ok) {
    document.getElementById("domainName").value = "";
    refreshPortal();
  }
});

document.getElementById("memberForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!activeInstitutionId) return;
  const status = document.getElementById("memberStatus");
  const res = await fetch(`/api/v1/institution-portal/${encodeURIComponent(activeInstitutionId)}/memberships`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      email: document.getElementById("memberEmail").value.trim(),
      member_role: document.getElementById("memberRole").value,
    }),
  });
  const data = await res.json();
  status.textContent = res.ok
    ? `Member #${data.user_id}${data.temporary_password ? ` ù temp password ${data.temporary_password}` : ""}`
    : errMessage(data);
  if (res.ok) refreshPortal();
});

document.getElementById("brandingForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!activeInstitutionId) return;
  const status = document.getElementById("brandingStatus");
  const res = await fetch(`/api/v1/institution-portal/${encodeURIComponent(activeInstitutionId)}/branding`, {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      branding: {
        primary_color: document.getElementById("brandColor").value.trim() || undefined,
        logo_url: document.getElementById("brandLogo").value.trim() || undefined,
      },
      contact_email: document.getElementById("brandEmail").value.trim() || null,
    }),
  });
  const data = await res.json();
  status.textContent = res.ok ? "Branding saved." : errMessage(data);
  if (res.ok) refreshPortal();
});

document.getElementById("accountForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!activeInstitutionId) return;
  const status = document.getElementById("accountStatus");
  const res = await fetch(`/api/v1/institution-portal/${encodeURIComponent(activeInstitutionId)}/official-accounts`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      platform: document.getElementById("accountPlatform").value.trim(),
      handle: document.getElementById("accountHandle").value.trim(),
    }),
  });
  const data = await res.json();
  status.textContent = res.ok ? `Added ${data.handle}` : errMessage(data);
  if (res.ok) {
    document.getElementById("accountHandle").value = "";
    refreshPortal();
  }
});

document.getElementById("keyForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!activeInstitutionId) return;
  const status = document.getElementById("keyStatus");
  const res = await fetch(`/api/v1/institution-portal/${encodeURIComponent(activeInstitutionId)}/api-keys`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ name: document.getElementById("keyName").value.trim() }),
  });
  const data = await res.json();
  status.textContent = res.ok ? `Created key (copy now): ${data.api_key}` : errMessage(data);
  if (res.ok) refreshPortal();
});

document.getElementById("partnerForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!activeInstitutionId) return;
  const status = document.getElementById("partnerStatus");
  const target = document.getElementById("partnerTarget").value.trim().toLowerCase();
  const res = await fetch("/api/v1/trust-network/relationships", {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      source_institution_id: activeInstitutionId,
      target_institution_id: target,
      status: "pending",
      policy_note: document.getElementById("partnerNote").value.trim(),
    }),
  });
  const data = await res.json();
  status.textContent = res.ok ? `Relationship #${data.id} created (pending)` : errMessage(data);
  if (res.ok) {
    document.getElementById("partnerTarget").value = "";
    refreshTrustNetwork();
  }
});

document.getElementById("alertForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!activeInstitutionId) return;
  const status = document.getElementById("alertStatus");
  const targets = document
    .getElementById("alertTargets")
    .value.split(",")
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
  const res = await fetch("/api/v1/trust-network/exchange/alerts", {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      alert_type: document.getElementById("alertType").value,
      title: document.getElementById("alertTitle").value.trim(),
      summary: document.getElementById("alertSummary").value.trim(),
      severity: document.getElementById("alertSeverity").value,
      source_institution_id: activeInstitutionId,
      target_institutions: targets,
    }),
  });
  const data = await res.json();
  status.textContent = res.ok ? `Shared alert #${data.id}` : errMessage(data);
  if (res.ok) {
    document.getElementById("alertTitle").value = "";
    document.getElementById("alertSummary").value = "";
    refreshTrustNetwork();
  }
});

loadInstitutionOptions();
const params = new URLSearchParams(window.location.search);
const preset = params.get("institution_id");
if (preset) {
  document.getElementById("institutionId").value = preset;
  activeInstitutionId = preset.toLowerCase();
  refreshPortal();
}
