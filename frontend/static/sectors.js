function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function loadPack() {
  const box = document.getElementById("packBox");
  const res = await fetch("/api/v1/country-pack");
  const data = await res.json();
  const pack = data.pack || {};
  const legal = pack.legal || {};
  box.className = "out history-detail is-ready";
  box.innerHTML = `
    <h3>${escapeHtml(pack.name || pack.pack_id)} (${escapeHtml(pack.iso_country || "")})</h3>
    <p class="muted">Tenant ${escapeHtml(pack.tenant_display_name || pack.tenant_id)} - locales ${(pack.supported_locales || []).join(", ")}</p>
    <p>${escapeHtml(legal.data_protection_note || "")}</p>
    <p class="muted">IdP: ${escapeHtml((pack.idp && pack.idp.notes) || "")}</p>
  `;
}

async function loadSectors() {
  const list = document.getElementById("sectorList");
  const res = await fetch("/api/v1/sectors");
  const data = await res.json();
  list.innerHTML = (data.sectors || [])
    .map((item) => {
      const band = item.enabled ? "low" : "medium";
      const state = item.enabled ? "ENABLED" : "OFF";
      return `
      <article class="history-item">
        <div class="history-item-top">
          <strong>${escapeHtml(item.name)}</strong>
          <span class="band ${band}">${state}</span>
        </div>
        <p class="muted">${escapeHtml(item.id)} - ${escapeHtml(item.description || "")}</p>
        ${
          item.enabled
            ? `<p><a href="/static/national.html">Open national analytics</a> - <a href="/static/ntoc.html">NTOC</a></p>`
            : ""
        }
      </article>`;
    })
    .join("") || "<p class='muted'>No sectors configured.</p>";
}

loadPack();
loadSectors();
