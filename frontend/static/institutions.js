function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function loadInstitutions() {
  const lead = document.getElementById("registryLead");
  const list = document.getElementById("institutionList");
  const res = await fetch("/api/v1/institutions");
  const data = await res.json();
  const institutions = data.institutions || [];

  lead.textContent = `${institutions.length} verified institutions in the MboaShield registry.`;
  list.innerHTML = institutions
    .map(
      (inst) => `
        <article class="history-item institution-card">
          <div class="history-item-top">
            <strong>${escapeHtml(inst.short_name)}</strong>
            <span class="band low">VERIFIED</span>
          </div>
          <p class="history-item-title">${escapeHtml(inst.name)}</p>
          <p class="muted">${escapeHtml((inst.handles || []).slice(0, 3).join(" · "))}</p>
          ${
            inst.url
              ? `<p><a href="${escapeHtml(inst.url)}" target="_blank" rel="noopener">Official website</a></p>`
              : ""
          }
        </article>
      `
    )
    .join("");
}

loadInstitutions();
