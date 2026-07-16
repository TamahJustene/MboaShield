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

function bandClass(status) {
  if (["open", "ai_analysis"].includes(status)) return "high";
  if (["analyst_review", "reviewing", "institution_review", "decision"].includes(status)) return "medium";
  return "low";
}

async function loadSummary() {
  const res = await fetch("/api/v1/analyst/summary");
  const data = await res.json();
  const counts = data.status_counts || {};
  const el = document.getElementById("analystSummary");
  el.innerHTML = Object.entries(counts)
    .map(([status, count]) => `<div class="stat-chip"><strong>${escapeHtml(count)}</strong><span>${escapeHtml(status)}</span></div>`)
    .join("") || "<p class='muted'>No incidents yet.</p>";
  document.getElementById("workflowPipeline").innerHTML = (data.workflow || [])
    .map((step) => `<li>${escapeHtml(step)}</li>`)
    .join("");
}

function renderCase(report, events) {
  const detail = document.getElementById("caseDetail");
  const actions = (report.next_actions || [])
    .map((status) => `<button type="button" class="btn-ghost status-action" data-status="${escapeHtml(status)}">${escapeHtml(status)}</button>`)
    .join("");
  const ai = report.ai_summary || {};
  detail.className = "out history-detail is-ready";
  detail.innerHTML = `
    <span class="band ${bandClass(report.status)}">${escapeHtml(String(report.status).toUpperCase())}</span>
    <h3 class="report-title">Incident #${escapeHtml(report.id)} · ${escapeHtml(report.report_type)}</h3>
    <section class="report-section">
      <span class="report-label">Description</span>
      <p class="report-copy">${escapeHtml(report.description)}</p>
    </section>
    <section class="report-section">
      <span class="report-label">AI summary</span>
      <p class="report-copy">${escapeHtml(ai.narrative || "No AI summary attached yet.")}</p>
      <p class="muted">Risk ${escapeHtml(ai.risk_score ?? "-")} · Confidence ${escapeHtml(ai.confidence ?? "-")}</p>
    </section>
    <section class="report-section">
      <span class="report-label">Public advisory draft</span>
      <textarea id="advisoryDraft" rows="3" placeholder="Optional public advisory text">${escapeHtml(report.public_advisory || "")}</textarea>
    </section>
    <section class="report-section">
      <span class="report-label">Decision note</span>
      <textarea id="decisionDraft" rows="2" placeholder="Decision summary">${escapeHtml(report.decision_summary || "")}</textarea>
    </section>
    <section class="report-section">
      <span class="report-label">Advance workflow</span>
      <div class="chip-row">${actions || "<p class='muted'>No further transitions.</p>"}</div>
    </section>
  `;

  detail.querySelectorAll(".status-action").forEach((btn) => {
    btn.onclick = async () => {
      const to_status = btn.getAttribute("data-status");
      const res = await fetch(`/api/v1/incidents/${report.id}/transition`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to_status,
          note: `Analyst advanced to ${to_status}`,
          public_advisory: document.getElementById("advisoryDraft").value || null,
          decision_summary: document.getElementById("decisionDraft").value || null,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.error?.message || err.detail || "Transition failed");
        return;
      }
      const updated = await res.json();
      const timeline = await fetch(`/api/v1/incidents/${report.id}/timeline`).then((r) => r.json());
      renderCase(updated, timeline.events || []);
      loadQueue();
      loadSummary();
    };
  });

  document.getElementById("caseTimeline").innerHTML = `
    <h3>Audit timeline</h3>
    <ol class="timeline-list">
      ${(events || [])
        .map(
          (event) => `
            <li>
              <strong>${escapeHtml(event.from_status || "start")} ? ${escapeHtml(event.to_status)}</strong>
              <p class="muted">${escapeHtml(formatTime(event.created_at))} · ${escapeHtml(event.actor_role || "system")}</p>
              <p class="report-copy">${escapeHtml(event.note || "")}</p>
            </li>
          `
        )
        .join("")}
    </ol>
  `;
}

async function openCase(id) {
  const [reportRes, timelineRes] = await Promise.all([
    fetch(`/api/v1/incidents/${id}`),
    fetch(`/api/v1/incidents/${id}/timeline`),
  ]);
  if (!reportRes.ok) return;
  renderCase(await reportRes.json(), (await timelineRes.json()).events || []);
}

async function loadQueue() {
  const list = document.getElementById("queueList");
  list.innerHTML = '<p class="report-copy muted">Loading...</p>';
  const res = await fetch("/api/v1/analyst/queue?limit=40");
  const data = await res.json();
  const reports = data.reports || [];
  document.getElementById("queueLead").textContent = `${reports.length} case${reports.length === 1 ? "" : "s"} require attention.`;
  list.innerHTML = reports
    .map(
      (report) => `
        <button type="button" class="history-item" data-id="${escapeHtml(report.id)}">
          <div class="history-item-top">
            <span class="band ${bandClass(report.status)}">${escapeHtml(report.status)}</span>
            <span class="muted">#${escapeHtml(report.id)}</span>
          </div>
          <p class="history-item-title">${escapeHtml(report.report_type)} · ${escapeHtml(report.description.slice(0, 80))}</p>
          <p class="muted">${escapeHtml(formatTime(report.updated_at || report.created_at))}</p>
        </button>
      `
    )
    .join("");
  list.querySelectorAll(".history-item").forEach((btn) => {
    btn.onclick = () => {
      list.querySelectorAll(".history-item").forEach((item) => item.classList.remove("active"));
      btn.classList.add("active");
      openCase(btn.getAttribute("data-id"));
    };
  });
}

document.getElementById("refreshAnalyst").onclick = () => {
  loadSummary();
  loadQueue();
};

loadSummary();
loadQueue();
