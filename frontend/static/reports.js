function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function getUserId() {
  return localStorage.getItem("mboashield_user_id");
}

function userHeaders(extra = {}) {
  const userId = getUserId();
  return userId ? { ...extra, "X-MboaShield-User-Id": userId } : extra;
}

function formatTime(iso) {
  if (!iso) return "-";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString();
}

function bandClass(status) {
  if (["open", "ai_analysis"].includes(status)) return "high";
  if (["analyst_review", "reviewing", "institution_review", "decision", "public_advisory"].includes(status)) {
    return "medium";
  }
  return "low";
}

let activeStatus = "";

async function loadTimeline(reportId) {
  const res = await fetch(`/api/v1/incidents/${reportId}/timeline`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.events || [];
}

function renderReportDetail(report, events = []) {
  const el = document.getElementById("reportDetail");
  const actions = (report.next_actions || [])
    .map((status) => `<button type="button" class="btn-ghost status-action" data-status="${escapeHtml(status)}">${escapeHtml(status)}</button>`)
    .join("");
  el.className = "out history-detail is-ready";
  el.innerHTML = `
    <span class="band ${bandClass(report.status)}">${escapeHtml(String(report.status).toUpperCase())}</span>
    <h3 class="report-title">Incident #${escapeHtml(report.id)} · ${escapeHtml(report.report_type)}</h3>
    <section class="report-section">
      <span class="report-label">Description</span>
      <p class="report-copy">${escapeHtml(report.description)}</p>
    </section>
    <section class="report-section">
      <span class="report-label">Linked check</span>
      <p class="report-copy">${
        report.verification_check_id
          ? `<a href="/static/history.html?check=${escapeHtml(report.verification_check_id)}">Check #${escapeHtml(report.verification_check_id)}</a>`
          : "None"
      }</p>
    </section>
    <section class="report-section">
      <span class="report-label">Reporter</span>
      <p class="report-copy">${report.user_id ? `User #${escapeHtml(report.user_id)}` : "Anonymous"}</p>
    </section>
    <section class="report-section">
      <span class="report-label">Created</span>
      <p class="report-copy">${escapeHtml(formatTime(report.created_at))}</p>
    </section>
    <section class="report-section">
      <span class="report-label">Reviewer note</span>
      <p class="report-copy">${escapeHtml(report.reviewer_note || "-")}</p>
    </section>
    <section class="report-section">
      <span class="report-label">Advance workflow</span>
      <div class="chip-row">${actions || "<p class='muted'>No further transitions.</p>"}</div>
      <p class="muted"><a href="/static/analyst.html">Open full analyst console</a></p>
    </section>
    <section class="report-section">
      <span class="report-label">Timeline</span>
      <ol class="timeline-list">
        ${
          events
            .map(
              (event) => `
                <li>
                  <strong>${escapeHtml(event.from_status || "start")} ? ${escapeHtml(event.to_status)}</strong>
                  <p class="muted">${escapeHtml(formatTime(event.created_at))}</p>
                </li>
              `
            )
            .join("") || "<li class='muted'>No events yet.</li>"
        }
      </ol>
    </section>
  `;

  el.querySelectorAll(".status-action").forEach((btn) => {
    btn.onclick = async () => {
      const status = btn.getAttribute("data-status");
      const res = await fetch(`/api/v1/incidents/${report.id}/transition`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to_status: status,
          note: `Status set to ${status} from reports UI`,
        }),
      });
      if (!res.ok) return;
      const updated = await res.json();
      const timeline = await loadTimeline(updated.id);
      renderReportDetail(updated, timeline);
      loadReports();
    };
  });
}

function renderReportsList(reports) {
  const list = document.getElementById("reportsList");
  const lead = document.getElementById("reportsLead");

  if (!reports.length) {
    lead.textContent = "No incident reports yet.";
    list.innerHTML = "";
    return;
  }

  lead.textContent = `${reports.length} report${reports.length === 1 ? "" : "s"} in queue.`;
  list.innerHTML = reports
    .map(
      (report) => `
        <button type="button" class="history-item" data-report-id="${escapeHtml(report.id)}">
          <div class="history-item-top">
            <span class="band ${bandClass(report.status)}">${escapeHtml(String(report.status).toUpperCase())}</span>
            <span class="muted">#${escapeHtml(report.id)}</span>
          </div>
          <p class="history-item-title">${escapeHtml(report.report_type)} · ${escapeHtml(report.description.slice(0, 90))}</p>
          <p class="muted">${escapeHtml(formatTime(report.created_at))}</p>
        </button>
      `
    )
    .join("");

  list.querySelectorAll(".history-item").forEach((btn) => {
    btn.onclick = async () => {
      list.querySelectorAll(".history-item").forEach((item) => item.classList.remove("active"));
      btn.classList.add("active");
      const id = btn.getAttribute("data-report-id");
      const res = await fetch(`/api/v1/incidents/${id}`);
      if (!res.ok) return;
      const report = await res.json();
      renderReportDetail(report, await loadTimeline(report.id));
    };
  });
}

async function loadReports() {
  const list = document.getElementById("reportsList");
  list.innerHTML = '<p class="report-copy muted">Loading...</p>';
  const query = activeStatus ? `?limit=30&status=${encodeURIComponent(activeStatus)}` : "?limit=30";
  const res = await fetch(`/api/v1/incidents${query}`);
  const data = await res.json();
  renderReportsList(data.reports || []);
}

document.querySelectorAll("#statusFilters .filter-chip").forEach((chip) => {
  chip.onclick = () => {
    document.querySelectorAll("#statusFilters .filter-chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    activeStatus = chip.getAttribute("data-status") || "";
    loadReports();
  };
});

document.getElementById("refreshReports").onclick = () => loadReports();

document.getElementById("incidentForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = document.getElementById("incidentFormStatus");
  const report_type = document.getElementById("reportType").value;
  const description = document.getElementById("reportDescription").value.trim();
  const checkRaw = document.getElementById("reportCheckId").value.trim();
  const verification_check_id = checkRaw ? Number(checkRaw) : null;

  if (description.length < 8) {
    status.textContent = "Please describe the incident in at least 8 characters.";
    return;
  }

  status.textContent = "Submitting report...";
  const res = await fetch("/api/v1/incidents", {
    method: "POST",
    headers: userHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      report_type,
      description,
      verification_check_id,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    status.textContent = err.error?.message || err.detail || "Could not submit report.";
    return;
  }

  const report = await res.json();
  status.textContent = `Incident #${report.id} submitted (${report.status}).`;
  document.getElementById("reportDescription").value = "";
  document.getElementById("reportCheckId").value = "";
  renderReportDetail(report, await loadTimeline(report.id));
  loadReports();
});

async function openFromQuery() {
  const params = new URLSearchParams(window.location.search);
  const checkId = params.get("check");
  if (checkId) {
    document.getElementById("reportCheckId").value = checkId;
  }
  const reportId = params.get("report");
  if (!reportId) return;
  const res = await fetch(`/api/v1/incidents/${encodeURIComponent(reportId)}`);
  if (!res.ok) return;
  const report = await res.json();
  renderReportDetail(report, await loadTimeline(report.id));
}

loadReports();
openFromQuery();
