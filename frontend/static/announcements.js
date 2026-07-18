function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function loadInstitutions() {
  const res = await fetch("/api/v1/institutions");
  const data = await res.json();
  document.getElementById("institutionOptions").innerHTML = (data.institutions || [])
    .map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.short_name)}</option>`)
    .join("");
}

async function loadAnnouncements() {
  const res = await fetch("/api/v1/announcements?limit=20");
  const data = await res.json();
  const list = document.getElementById("announcementList");
  if (!res.ok) {
    list.innerHTML = `<p class="muted">${escapeHtml(data.detail || "Could not load")}</p>`;
    return;
  }
  list.innerHTML = (data.announcements || [])
    .map(
      (item) => `
    <article class="history-item">
      <div class="history-item-top">
        <strong>${escapeHtml(item.title)}</strong>
        <span class="band ${item.status === "published" ? "low" : "medium"}">${escapeHtml(item.status)}</span>
      </div>
      <p class="muted"><code>${escapeHtml(item.announcement_id)}</code>  -  ${escapeHtml(item.institution_id)}  -  v${escapeHtml(item.current_version)}</p>
      <p>
        <a href="/verify/a/${encodeURIComponent(item.announcement_id)}" target="_blank" rel="noopener">Public verify</a>
         -  <a href="/static/verify-announcement.html?a=${encodeURIComponent(item.announcement_id)}">UI verify</a>
      </p>
    </article>`
    )
    .join("") || "<p class='muted'>No announcements yet.</p>";
}

document.getElementById("publishForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = document.getElementById("publishStatus");
  const institutionId = document.getElementById("institutionId").value.trim();
  const title = document.getElementById("title").value.trim();
  const body = document.getElementById("body").value.trim();
  status.textContent = "Creating draft...";
  const created = await fetch("/api/v1/announcements", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ institution_id: institutionId, title, body, locale: "fr" }),
  });
  const createdData = await created.json();
  if (!created.ok) {
    status.textContent = createdData.detail || createdData.error?.message || "Create failed";
    return;
  }
  const announcementId = createdData.announcement_id;
  status.textContent = "Publishing...";
  const published = await fetch(`/api/v1/announcements/${encodeURIComponent(announcementId)}/publish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  const pub = await published.json();
  if (!published.ok) {
    status.textContent = pub.detail || "Publish failed";
    return;
  }
  status.textContent = `Published ${announcementId}`;
  const panel = document.getElementById("publishResult");
  panel.className = "out history-detail is-ready";
  panel.innerHTML = `
    <p>Verify URL: <a href="${escapeHtml(pub.verify_url)}" target="_blank" rel="noopener">${escapeHtml(pub.verify_url)}</a></p>
    <p class="muted">QR payload: ${escapeHtml(JSON.stringify(pub.qr))}</p>
  `;
  loadAnnouncements();
});

loadInstitutions();
loadAnnouncements();
