function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function authHeaders(extra = {}) {
  const token = localStorage.getItem("mboashield_access_token");
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
}

let activeCaseId = null;

function queryCaseId() {
  const params = new URLSearchParams(window.location.search);
  const value = params.get("case_id");
  return value ? Number(value) : null;
}

async function loadCases() {
  const res = await fetch("/api/v1/cases?limit=30", { headers: authHeaders() });
  const data = await res.json();
  const list = document.getElementById("caseSearchList");
  if (!res.ok) {
    list.innerHTML = `<p class='muted'>${escapeHtml(data.detail || data.error?.message || "Could not load cases")}</p>`;
    return;
  }
  list.innerHTML = (data.cases || [])
    .map(
      (item) => `
      <article class="history-item">
        <div class="history-item-top">
          <strong>#${item.id} ${escapeHtml(item.title)}</strong>
          <button type="button" class="btn-ghost" data-case="${item.id}">Open</button>
        </div>
        <p class="muted">${escapeHtml(item.status)} · ${escapeHtml(item.priority)} · ${escapeHtml(item.region || "Unspecified")}</p>
      </article>`
    )
    .join("") || "<p class='muted'>No cases yet.</p>";
  list.querySelectorAll("[data-case]").forEach((btn) => {
    btn.onclick = () => openWorkspace(Number(btn.getAttribute("data-case")));
  });
}

async function openWorkspace(caseId) {
  activeCaseId = caseId;
  const res = await fetch(`/api/v1/cases/${caseId}/workspace`, { headers: authHeaders() });
  const data = await res.json();
  const panel = document.getElementById("workspace");
  if (!res.ok) {
    panel.innerHTML = `<p class="report-copy">${escapeHtml(data.detail || data.error?.message || "Workspace unavailable")}</p>`;
    return;
  }
  const c = data.case || {};
  const evidence = data.evidence?.evidence_items || [];
  const vault = data.evidence?.vault_items || [];
  const notes = data.notes || [];
  const timeline = data.timeline || [];
  panel.className = "out history-detail is-ready";
  panel.innerHTML = `
    <h3>#${c.id} ${escapeHtml(c.title)}</h3>
    <p>${escapeHtml(c.summary || "No summary")}</p>
    <p class="muted">Status ${escapeHtml(c.status)} · Priority ${escapeHtml(c.priority)} · Incident ${escapeHtml(c.incident_id || "none")}</p>
    <h4>Linked verification</h4>
    ${(evidence.map((item) => `<p>#${item.id} ${escapeHtml(item.check_type)} · risk ${escapeHtml(item.risk_score)} (${escapeHtml(item.risk_band)})</p>`).join("") || "<p class='muted'>No linked verification check.</p>")}
    <h4>Vault evidence</h4>
    ${(vault.map((item) => `<p><code>${escapeHtml(item.evidence_id)}</code> ${escapeHtml(item.title)} · ${escapeHtml(item.filename)} · sha256 ${escapeHtml(String(item.sha256).slice(0, 12))}…</p>`).join("") || "<p class='muted'>No vault items yet. Upload below.</p>")}
    <h4>Notes</h4>
    ${notes.map((note) => `<p><strong>${escapeHtml(note.author_role || "analyst")}</strong>: ${escapeHtml(note.body)}</p>`).join("") || "<p class='muted'>No notes yet.</p>"}
    <h4>Incident timeline</h4>
    ${timeline.map((event) => `<p class="muted">${escapeHtml(event.created_at)} · ${escapeHtml(event.from_status || "-")} ? ${escapeHtml(event.to_status)}</p>`).join("") || "<p class='muted'>No incident timeline.</p>"}
  `;
  document.getElementById("noteForm").classList.remove("hidden");
  document.getElementById("assignForm").classList.remove("hidden");
  document.getElementById("evidenceForm").classList.remove("hidden");
}

document.getElementById("createCaseForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = document.getElementById("createCaseStatus");
  const incidentRaw = document.getElementById("caseIncidentId").value;
  const payload = {
    title: document.getElementById("caseTitle").value.trim(),
    summary: document.getElementById("caseSummary").value.trim() || null,
    priority: document.getElementById("casePriority").value,
    region: document.getElementById("caseRegion").value.trim() || null,
  };
  if (incidentRaw) payload.incident_id = Number(incidentRaw);
  const res = await fetch("/api/v1/cases", {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    status.textContent = data.detail || data.error?.message || "Create failed";
    return;
  }
  status.textContent = `Created case #${data.id}`;
  loadCases();
  openWorkspace(data.id);
});

document.getElementById("noteForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!activeCaseId) return;
  await fetch(`/api/v1/cases/${activeCaseId}/notes`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ body: document.getElementById("noteBody").value.trim() }),
  });
  document.getElementById("noteBody").value = "";
  openWorkspace(activeCaseId);
});

document.getElementById("assignForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!activeCaseId) return;
  const status = document.getElementById("assignStatus");
  const res = await fetch(`/api/v1/cases/${activeCaseId}/assign`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ assignee_user_id: Number(document.getElementById("assigneeId").value) }),
  });
  const data = await res.json();
  status.textContent = res.ok ? "Assigned." : data.detail || data.error?.message || "Assign failed";
  if (res.ok) openWorkspace(activeCaseId);
});

document.getElementById("evidenceForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!activeCaseId) return;
  const status = document.getElementById("evidenceStatus");
  const fileInput = document.getElementById("evidenceFile");
  const file = fileInput.files?.[0];
  if (!file) {
    status.textContent = "Choose a file";
    return;
  }
  const form = new FormData();
  form.append("title", document.getElementById("evidenceTitle").value.trim());
  form.append("filename", file.name);
  form.append("case_id", String(activeCaseId));
  form.append("file", file);
  const res = await fetch("/api/v1/evidence", {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    status.textContent = data.detail || data.error?.message || "Upload failed";
    return;
  }
  status.textContent = `Registered ${data.evidence_id}`;
  document.getElementById("evidenceTitle").value = "";
  fileInput.value = "";
  openWorkspace(activeCaseId);
});

document.getElementById("refreshCases").onclick = loadCases;

loadCases();
const initial = queryCaseId();
if (initial) openWorkspace(initial);
