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

function bandClass(level) {
  if (level === "critical" || level === "high") return "high";
  if (level === "elevated") return "medium";
  return "low";
}

async function loadNtoc() {
  const dashRes = await fetch("/api/v1/ntoc/dashboard", { headers: authHeaders() });
  const dash = await dashRes.json();
  if (!dashRes.ok) {
    document.getElementById("threatLevel").textContent = dash.detail || "NTOC unavailable";
    return;
  }

  const threat = dash.threat_level || {};
  document.getElementById("threatLevel").innerHTML = `
    <div class="stat-card"><span class="stat-label">Level</span><strong class="band ${bandClass(threat.level)}">${escapeHtml(threat.level)}</strong></div>
    <div class="stat-card"><span class="stat-label">Score</span><strong>${escapeHtml(threat.score)}</strong></div>
    <div class="stat-card"><span class="stat-label">Open queue</span><strong>${escapeHtml(dash.queue?.active_total)}</strong></div>
    <div class="stat-card"><span class="stat-label">Open cases</span><strong>${escapeHtml(dash.cases?.open_count)}</strong></div>
  `;
  document.getElementById("ntocGenerated").textContent = `Generated ${dash.generated_at || ""}`;

  const counts = dash.queue?.status_counts || {};
  document.getElementById("queuePanel").innerHTML = Object.entries(counts)
    .map(([status, count]) => `<p><strong>${escapeHtml(status)}</strong>: ${escapeHtml(count)}</p>`)
    .join("") || "<p class='muted'>No incidents yet.</p>";

  const regions = dash.regional_map?.regions || [];
  document.getElementById("regionMap").innerHTML = regions
    .map((region) => {
      const width = Math.max(8, region.intensity || 0);
      return `<div class="heat-row"><span>${escapeHtml(region.region)}</span><div class="heat-bar-track"><div class="heat-bar-fill" style="width:${width}%"></div></div><em>${escapeHtml(region.incident_count)}</em></div>`;
    })
    .join("");

  document.getElementById("caseList").innerHTML = (dash.cases?.recent || [])
    .map(
      (item) => `
      <article class="history-item">
        <div class="history-item-top">
          <strong><a href="/static/investigation.html?case_id=${item.id}">#${item.id} ${escapeHtml(item.title)}</a></strong>
          <span class="band ${bandClass(item.priority)}">${escapeHtml(item.status)}</span>
        </div>
        <p class="muted">${escapeHtml(item.region || "Unspecified")} ù priority ${escapeHtml(item.priority)}</p>
      </article>`
    )
    .join("") || "<p class='muted'>No cases yet. Open Investigation workspace to create one.</p>";

  document.getElementById("healthList").innerHTML = (dash.institution_health || [])
    .map(
      (item) => `
      <article class="history-item">
        <div class="history-item-top">
          <strong>${escapeHtml(item.short_name || item.name)}</strong>
          <span class="band ${item.health_score < 60 ? "high" : item.health_score < 80 ? "medium" : "low"}">${escapeHtml(item.health_score)}</span>
        </div>
        <p class="muted">Open incidents ${escapeHtml(item.open_incidents)} ù high-risk checks ${escapeHtml(item.high_risk_checks)}</p>
      </article>`
    )
    .join("") || "<p class='muted'>No institutions.</p>";
}

async function loadNotifications() {
  const res = await fetch("/api/v1/notifications?audience=analyst", { headers: authHeaders() });
  const data = await res.json();
  if (!res.ok) {
    document.getElementById("notificationBell").textContent = "Sign in as analyst when AUTH_ENFORCE=true.";
    return;
  }
  document.getElementById("notificationBell").innerHTML = `<strong>${escapeHtml(data.unread || 0)}</strong> unread ù ${escapeHtml(data.count || 0)} total`;
  document.getElementById("notificationList").innerHTML = (data.notifications || [])
    .slice(0, 8)
    .map(
      (item) => `
      <article class="history-item">
        <div class="history-item-top">
          <strong>${escapeHtml(item.title)}</strong>
          ${item.read ? "" : `<button type="button" class="btn-ghost" data-note="${item.id}">Mark read</button>`}
        </div>
        <p class="muted">${escapeHtml(item.body)}</p>
      </article>`
    )
    .join("") || "<p class='muted'>No notifications.</p>";

  document.querySelectorAll("[data-note]").forEach((btn) => {
    btn.onclick = async () => {
      await fetch(`/api/v1/notifications/${btn.getAttribute("data-note")}/read`, {
        method: "POST",
        headers: authHeaders(),
      });
      loadNotifications();
    };
  });
}

document.getElementById("refreshNtoc").onclick = () => {
  loadNtoc();
  loadNotifications();
};

loadNtoc();
loadNotifications();
