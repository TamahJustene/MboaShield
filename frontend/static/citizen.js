function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatTime(iso) {
  if (!iso) return "-";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString();
}

function getUserId() {
  return localStorage.getItem("mboashield_user_id");
}

function setUserId(id) {
  localStorage.setItem("mboashield_user_id", String(id));
}

function userHeaders(extra = {}) {
  const userId = getUserId();
  return userId ? { ...extra, "X-MboaShield-User-Id": userId } : extra;
}

function trustScoreFromRisk(riskScore) {
  if (riskScore == null || Number.isNaN(Number(riskScore))) return null;
  return Math.max(0, Math.min(100, 100 - Number(riskScore)));
}

async function loadDashboard() {
  const userId = getUserId();
  const identity = document.getElementById("citizenIdentity");
  if (!userId) {
    identity.textContent = "Create a profile to personalize your dashboard.";
    return;
  }
  const res = await fetch("/api/v1/citizen/dashboard?limit=20", { headers: userHeaders() });
  if (!res.ok) {
    identity.textContent = "Could not load dashboard for this profile.";
    return;
  }
  const data = await res.json();
  identity.textContent = `${data.user.display_name} ù User #${data.user.id} ù role ${data.user.role}`;

  document.getElementById("checksLead").textContent = `${data.checks_count} recent check${data.checks_count === 1 ? "" : "s"}.`;
  document.getElementById("checksList").innerHTML = (data.checks || [])
    .map(
      (check) => {
        const trustScore = trustScoreFromRisk(check.risk_score);
        const trustLabel =
          trustScore != null ? ` ∑ trust ${trustScore}/100` : "";
        return `
        <a class="history-item" href="/static/history.html?check=${escapeHtml(check.id)}">
          <div class="history-item-top">
            <span class="band ${check.risk_band || "low"}">${escapeHtml((check.risk_band || "n/a").toUpperCase())}</span>
            <span class="muted">#${escapeHtml(check.id)}</span>
          </div>
          <p class="history-item-title">${escapeHtml(check.check_type)}${escapeHtml(trustLabel)}</p>
          <p class="muted">${escapeHtml(formatTime(check.created_at))}</p>
        </a>
      `;
      }
    )
    .join("") || "<p class='muted'>No checks linked yet. Run a verification from the home app.</p>";

  document.getElementById("incidentsLead").textContent = `${data.incidents_count} report${data.incidents_count === 1 ? "" : "s"}.`;
  document.getElementById("incidentsList").innerHTML = (data.incidents || [])
    .map(
      (report) => `
        <a class="history-item" href="/static/reports.html?report=${escapeHtml(report.id)}">
          <div class="history-item-top">
            <span class="band medium">${escapeHtml(report.status)}</span>
            <span class="muted">#${escapeHtml(report.id)}</span>
          </div>
          <p class="history-item-title">${escapeHtml(report.report_type)}</p>
          <p class="muted">${escapeHtml(formatTime(report.created_at))}</p>
        </a>
      `
    )
    .join("") || "<p class='muted'>No incident reports yet.</p>";

  document.getElementById("certificatesList").innerHTML = (data.certificates || [])
    .map(
      (cert) => `
        <div class="history-item">
          <p class="history-item-title">${escapeHtml(cert.lesson_title_en)}</p>
          <p class="muted">${escapeHtml(cert.certificate_id)} ù ${escapeHtml(cert.issued_on)}</p>
        </div>
      `
    )
    .join("") || "<p class='muted'>Complete an Ambassador lesson to earn a certificate.</p>";
}

document.getElementById("citizenProfileForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = document.getElementById("citizenProfileStatus");
  const display_name = document.getElementById("citizenName").value.trim();
  const email = document.getElementById("citizenEmail").value.trim() || null;
  status.textContent = "Saving profile...";
  const res = await fetch("/api/v1/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ display_name, email }),
  });
  if (!res.ok) {
    status.textContent = "Could not save profile.";
    return;
  }
  const user = await res.json();
  setUserId(user.id);
  status.textContent = `Profile linked as User #${user.id}.`;
  loadDashboard();
});

loadDashboard();
