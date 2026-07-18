function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function runVerify(announcementId, version) {
  const params = new URLSearchParams();
  if (version) params.set("v", String(version));
  const suffix = params.toString() ? `?${params}` : "";
  const res = await fetch(`/verify/a/${encodeURIComponent(announcementId)}${suffix}`);
  const data = await res.json();
  const panel = document.getElementById("verifyResult");
  if (!res.ok) {
    panel.innerHTML = `<p class="report-copy">${escapeHtml(data.detail || data.error?.message || "Not found")}</p>`;
    return;
  }
  const band = data.valid ? "low" : "high";
  const label = data.valid ? "AUTHENTIC" : data.status === "revoked" ? "REVOKED" : "NOT VERIFIED";
  panel.className = "out history-detail is-ready";
  panel.innerHTML = `
    <div class="history-item-top">
      <strong>${escapeHtml(label)}</strong>
      <span class="band ${band}">${escapeHtml(data.authenticity || data.status)}</span>
    </div>
    <p><strong>${escapeHtml(data.title || "Announcement")}</strong></p>
    <p class="muted">${escapeHtml(data.institution?.name || "")}  -  v${escapeHtml(data.version)}  -  ${escapeHtml(data.published_at || "")}</p>
    <p>${escapeHtml(data.body || data.message || "")}</p>
    <p class="muted">Signature valid: ${escapeHtml(data.signature_valid)}  -  certainty: none (cryptographic check only)</p>
    <p><a href="/verify/a/${encodeURIComponent(announcementId)}/certificate" target="_blank" rel="noopener">Download JSON certificate</a></p>
  `;
}

document.getElementById("verifyForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = document.getElementById("announcementId").value.trim();
  const version = document.getElementById("versionNo").value;
  await runVerify(id, version ? Number(version) : null);
});

const params = new URLSearchParams(window.location.search);
const pathMatch = window.location.pathname.match(/\/verify-announcement\.html$/);
const preset = params.get("a") || params.get("announcement_id");
if (preset) {
  document.getElementById("announcementId").value = preset;
  const v = params.get("v");
  if (v) document.getElementById("versionNo").value = v;
  runVerify(preset, v ? Number(v) : null);
}
