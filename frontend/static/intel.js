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

async function loadPolicy() {
  const res = await fetch("/api/v1/intel/source-classes");
  const data = await res.json();
  document.getElementById("policyBox").innerHTML = `
    <p>${escapeHtml(data.policy)}</p>
    <p><strong>Allowed:</strong> ${escapeHtml((data.allowed || []).join(", "))}</p>
    <p><strong>Forbidden:</strong> ${escapeHtml((data.forbidden || []).join(", "))}</p>
  `;
}

async function loadSources() {
  const res = await fetch("/api/v1/intel/sources", { headers: authHeaders() });
  const data = await res.json();
  const list = document.getElementById("sourceList");
  if (!res.ok) {
    list.innerHTML = `<p class="muted">${escapeHtml(data.detail || "Unable to load sources")}</p>`;
    return;
  }
  list.innerHTML = (data.sources || [])
    .map(
      (source) => `
      <article class="history-item">
        <div class="history-item-top">
          <strong>#${source.id} ${escapeHtml(source.name)}</strong>
          <span class="band ${source.enabled ? "low" : "high"}">${source.enabled ? "ON" : "OFF"}</span>
        </div>
        <p class="muted">${escapeHtml(source.source_class)} · ${escapeHtml(source.egress_host)} · ${escapeHtml(source.tos_reference)}</p>
        <button type="button" class="btn-ghost" data-ingest="${source.id}">Ingest</button>
      </article>`
    )
    .join("") || "<p class='muted'>No sources yet.</p>";
  list.querySelectorAll("[data-ingest]").forEach((btn) => {
    btn.onclick = async () => {
      const id = btn.getAttribute("data-ingest");
      const ingest = await fetch(`/api/v1/intel/sources/${id}/ingest`, {
        method: "POST",
        headers: authHeaders(),
      });
      const body = await ingest.json();
      document.getElementById("intelOut").className = "out history-detail is-ready";
      document.getElementById("intelOut").textContent = JSON.stringify(body, null, 2);
      loadItems();
    };
  });
}

async function loadItems() {
  const res = await fetch("/api/v1/intel/items?limit=20", { headers: authHeaders() });
  const data = await res.json();
  document.getElementById("itemList").innerHTML = (data.items || [])
    .map(
      (item) => `
      <article class="history-item">
        <strong>${escapeHtml(item.title)}</strong>
        <p class="muted">${escapeHtml(item.url || "")}</p>
      </article>`
    )
    .join("") || "<p class='muted'>No intel items.</p>";

  const camps = await fetch("/api/v1/intel/campaigns", { headers: authHeaders() }).then((r) => r.json());
  document.getElementById("campaignList").innerHTML = (camps.campaigns || [])
    .map(
      (c) => `
      <article class="history-item">
        <strong>${escapeHtml(c.name)}</strong>
        <p class="muted">${escapeHtml(c.summary || "")}</p>
      </article>`
    )
    .join("") || "<p class='muted'>No campaigns yet. Run correlation after ingest.</p>";
}

document.getElementById("sourceForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = document.getElementById("sourceStatus");
  const payload = {
    name: document.getElementById("sourceName").value.trim(),
    source_class: document.getElementById("sourceClass").value,
    endpoint_url: document.getElementById("sourceUrl").value.trim(),
    tos_reference: document.getElementById("sourceTos").value.trim(),
    license: document.getElementById("sourceLicense").value.trim() || "unknown",
  };
  const res = await fetch("/api/v1/intel/sources", {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  status.textContent = res.ok ? `Created source #${data.id}` : data.detail || "Create failed";
  if (res.ok) loadSources();
});

document.getElementById("refreshSources").onclick = loadSources;
document.getElementById("runCorrelate").onclick = async () => {
  const res = await fetch("/api/v1/intel/correlate", { method: "POST", headers: authHeaders() });
  const data = await res.json();
  document.getElementById("intelOut").className = "out history-detail is-ready";
  document.getElementById("intelOut").textContent = JSON.stringify(data, null, 2);
  loadItems();
};
document.getElementById("loadReport").onclick = async () => {
  const res = await fetch("/api/v1/intel/reports/national", { headers: authHeaders() });
  const data = await res.json();
  document.getElementById("intelOut").className = "out history-detail is-ready";
  document.getElementById("intelOut").textContent = data.markdown || JSON.stringify(data, null, 2);
};

loadPolicy();
loadSources();
loadItems();
