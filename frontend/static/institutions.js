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

  lead.textContent = `${institutions.length} institutions in the MboaShield registry.`;
  list.innerHTML = institutions
    .map(
      (inst) => `
        <article class="history-item institution-card" data-id="${escapeHtml(inst.id)}">
          <div class="history-item-top">
            <strong>${escapeHtml(inst.short_name)}</strong>
            <span class="band ${inst.verified ? "low" : "medium"}">${inst.verified ? "VERIFIED" : "UNVERIFIED"}</span>
          </div>
          <p class="history-item-title">${escapeHtml(inst.name)}</p>
          <p class="muted">${escapeHtml((inst.handles || []).slice(0, 4).join(" · ") || "No handles")}</p>
          ${
            inst.url
              ? `<p><a href="${escapeHtml(inst.url)}" target="_blank" rel="noopener">Official website</a></p>`
              : ""
          }
          <button type="button" class="btn-ghost edit-institution" data-id="${escapeHtml(inst.id)}">Edit in form</button>
          <a class="btn-ghost" href="/static/institution-portal.html?institution_id=${escapeHtml(inst.id)}">Open portal</a>
        </article>
      `
    )
    .join("");

  list.querySelectorAll(".edit-institution").forEach((btn) => {
    btn.onclick = async () => {
      const id = btn.getAttribute("data-id");
      const res = await fetch(`/api/v1/institutions/${encodeURIComponent(id)}`);
      if (!res.ok) return;
      const inst = await res.json();
      document.getElementById("instId").value = inst.id;
      document.getElementById("instName").value = inst.name;
      document.getElementById("instShort").value = inst.short_name;
      document.getElementById("instUrl").value = inst.url || "";
      document.getElementById("instHandles").value = (inst.handles || []).join(", ");
      document.getElementById("instVerified").checked = !!inst.verified;
    };
  });
}

const adminForm = document.getElementById("institutionAdminForm");
if (adminForm) {
  adminForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const status = document.getElementById("institutionAdminStatus");
    const payload = {
      id: document.getElementById("instId").value.trim().toLowerCase(),
      name: document.getElementById("instName").value.trim(),
      short_name: document.getElementById("instShort").value.trim(),
      url: document.getElementById("instUrl").value.trim() || null,
      verified: document.getElementById("instVerified").checked,
      handles: document
        .getElementById("instHandles")
        .value.split(",")
        .map((item) => item.trim())
        .filter(Boolean),
    };
    status.textContent = "Saving...";
    const existing = await fetch(`/api/v1/institutions/${encodeURIComponent(payload.id)}`);
    let res;
    if (existing.ok) {
      res = await fetch(`/api/v1/institutions/${encodeURIComponent(payload.id)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: payload.name,
          short_name: payload.short_name,
          url: payload.url,
          verified: payload.verified,
          handles: payload.handles,
        }),
      });
    } else {
      res = await fetch("/api/v1/institutions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      status.textContent = err.error?.message || err.detail || "Save failed";
      return;
    }
    status.textContent = `Saved ${payload.short_name}.`;
    loadInstitutions();
  });
}

loadInstitutions();
