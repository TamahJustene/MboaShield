function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function entriesList(obj, emptyText) {
  const entries = Object.entries(obj || {});
  if (!entries.length) return `<p class="muted">${escapeHtml(emptyText)}</p>`;
  return `<ul class="timeline-list">${entries
    .map(([key, value]) => `<li><strong>${escapeHtml(key)}</strong>: ${escapeHtml(value)}</li>`)
    .join("")}</ul>`;
}

function renderOverview(overview) {
  const el = document.getElementById("nationalOverview");
  const items = [
    ["Checks", overview.checks_total],
    ["Incidents", overview.incidents_total],
    ["Open queue", overview.open_queue],
    ["Users", overview.users_total],
    ["Certificates", overview.certificates_total],
    ["AI labels", overview.feedback_total],
  ];
  el.innerHTML = items
    .map(
      ([label, value]) =>
        `<div class="stat-chip"><strong>${escapeHtml(value ?? 0)}</strong><span>${escapeHtml(label)}</span></div>`
    )
    .join("");
}

function renderHeatMap(rows) {
  const el = document.getElementById("regionHeatMap");
  if (!rows.length) {
    el.innerHTML = "<p class='muted'>No regional incident data yet.</p>";
    return;
  }
  el.innerHTML = rows
    .map((row) => {
      const width = Math.max(8, Math.round((row.intensity || 0) * 100));
      return `
        <div class="heat-row">
          <span class="heat-label">${escapeHtml(row.region)}</span>
          <div class="heat-bar-track"><div class="heat-bar-fill" style="width:${width}%"></div></div>
          <span class="heat-count">${escapeHtml(row.incident_count)}</span>
        </div>
      `;
    })
    .join("");
}

async function loadNational() {
  const res = await fetch("/api/v1/analytics/national");
  if (!res.ok) {
    document.getElementById("nationalOverview").textContent = "Could not load national analytics.";
    return;
  }
  const data = await res.json();
  renderOverview(data.overview || {});
  document.getElementById("nationalGenerated").textContent = `Generated ${data.generated_at || ""}`;

  document.getElementById("threatTrends").innerHTML = `
    <p><strong>By check type</strong></p>
    ${entriesList(data.threat_trends?.by_check_type, "No checks yet.")}
    <p><strong>By threat category</strong></p>
    ${entriesList(data.threat_trends?.by_threat_category, "No threat categories yet.")}
    <p><strong>Checks by day</strong></p>
    ${entriesList(data.threat_trends?.checks_by_day, "No daily activity yet.")}
  `;

  document.getElementById("deepfakeTrends").innerHTML = `
    <p>Media checks: <strong>${escapeHtml(data.deepfake_trends?.media_checks ?? 0)}</strong></p>
    <p>Audio checks: <strong>${escapeHtml(data.deepfake_trends?.audio_checks ?? 0)}</strong></p>
    <p><strong>High-risk media/audio by day</strong></p>
    ${entriesList(data.deepfake_trends?.high_risk_media_audio_by_day, "No deepfake-risk signals yet.")}
  `;

  renderHeatMap(data.regional_heat_map || []);

  const targets = data.institution_attacks?.top_targets || [];
  document.getElementById("institutionAttacks").innerHTML = targets.length
    ? `<ul class="timeline-list">${targets
        .map((item) => `<li><strong>${escapeHtml(item.institution)}</strong>: ${escapeHtml(item.count)}</li>`)
        .join("")}</ul>`
    : "<p class='muted'>No impersonation pressure recorded yet.</p>";

  document.getElementById("incidentTimeline").innerHTML = `
    <p><strong>By status</strong></p>
    ${entriesList(data.incident_timeline?.by_status, "No incidents yet.")}
    <p><strong>By day</strong></p>
    ${entriesList(data.incident_timeline?.by_day, "No timeline points yet.")}
    <p><strong>Response time</strong></p>
    <p>Sample: ${escapeHtml(data.response_time?.sample_size ?? 0)}  -  Avg hours: ${escapeHtml(
      data.response_time?.average_hours ?? "-"
    )}  -  Median hours: ${escapeHtml(data.response_time?.median_hours ?? "-")}</p>
  `;

  const ai = data.ai_accuracy || {};
  document.getElementById("aiAccuracy").innerHTML = `
    <p>Accuracy: <strong>${escapeHtml(ai.accuracy ?? "n/a")}</strong></p>
    <p>Precision: <strong>${escapeHtml(ai.precision ?? "n/a")}</strong></p>
    <p>False positive rate: <strong>${escapeHtml(ai.false_positive_rate ?? "n/a")}</strong></p>
    <p><strong>Labeled feedback</strong></p>
    ${entriesList(ai.labeled_feedback, "No analyst labels yet.")}
    <p class="muted">${escapeHtml(ai.honesty_note || "")}</p>
  `;

  const part = data.citizen_participation || {};
  document.getElementById("participation").innerHTML = `
    <p>Users: <strong>${escapeHtml(part.users_total ?? 0)}</strong></p>
    <p>Checks linked to users: <strong>${escapeHtml(part.checks_linked_to_users ?? 0)}</strong></p>
    <p>Incidents linked to users: <strong>${escapeHtml(part.incidents_linked_to_users ?? 0)}</strong></p>
    <p>Certificates issued: <strong>${escapeHtml(part.certificates_issued ?? 0)}</strong></p>
    <p>Check participation rate: <strong>${escapeHtml(part.participation_rate_checks ?? 0)}</strong></p>
  `;
}

document.getElementById("refreshNational").onclick = () => loadNational();

document.getElementById("feedbackForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = document.getElementById("feedbackStatus");
  status.textContent = "Submitting feedback...";
  const res = await fetch("/api/v1/analytics/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      verification_check_id: Number(document.getElementById("feedbackCheckId").value),
      label: document.getElementById("feedbackLabel").value,
      note: document.getElementById("feedbackNote").value.trim() || null,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    status.textContent = err.error?.message || err.detail || "Feedback failed";
    return;
  }
  status.textContent = "Feedback recorded.";
  loadNational();
});

loadNational();
