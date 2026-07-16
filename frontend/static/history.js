function getUserId() {
  return localStorage.getItem("mboashield_user_id");
}

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

function checkSummaryInput(check) {
  const input = check.input || {};
  if (input.text) return input.text.slice(0, 80);
  if (input.handle) return input.handle;
  if (input.filename) return input.filename;
  return "No input summary";
}

function listHtml(items) {
  if (!items?.length) return '<p class="report-copy">-</p>';
  return `<ul class="report-list">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function renderCheckDetail(check) {
  const el = document.getElementById("checkDetail");
  const band = check.risk_band || "low";
  const signals = check.signals || [];
  const result = check.result || {};
  const reasons = result.reasons || [];

  el.className = "out history-detail is-ready";
  el.innerHTML = `
    <span class="band ${escapeHtml(band)}">${escapeHtml(String(band).toUpperCase())} ù ${escapeHtml(check.risk_score ?? "-")}/100</span>
    <h3 class="report-title">Check #${escapeHtml(check.id)} ù ${escapeHtml(check.check_type)}</h3>
    <section class="report-section">
      <span class="report-label">When</span>
      <p class="report-copy">${escapeHtml(formatTime(check.created_at))}</p>
    </section>
    <section class="report-section">
      <span class="report-label">Input</span>
      <p class="report-copy">${escapeHtml(checkSummaryInput(check))}</p>
    </section>
    <section class="report-section">
      <span class="report-label">Recommended action</span>
      <p class="report-copy">${escapeHtml(result.advice || "-")}</p>
    </section>
    <section class="report-section">
      <span class="report-label">Signals (${signals.length})</span>
      ${
        signals.length
          ? `<ul class="report-list">${signals
              .map(
                (s) =>
                  `<li><strong>${escapeHtml(s.signal_type)}</strong>: ${escapeHtml(s.signal_label)}</li>`
              )
              .join("")}</ul>`
          : '<p class="report-copy">No normalized signals stored.</p>'
      }
    </section>
    <section class="report-section">
      <span class="report-label">Reasons</span>
      ${listHtml(reasons)}
    </section>
    <section class="report-section">
      <span class="report-label">Escalate</span>
      <p class="report-copy"><a href="/static/reports.html?check=${escapeHtml(check.id)}">Report this check as an incident</a></p>
    </section>
    ${
      result.ai_analysis
        ? `<section class="report-section ai-block">
            <span class="report-label">AI analysis</span>
            <p class="report-copy"><strong>${escapeHtml(result.ai_analysis.narrative || "")}</strong></p>
            <p class="report-copy muted">Confidence ${escapeHtml(result.ai_analysis.confidence ?? "-")}/100</p>
            ${listHtml(result.ai_analysis.threat_categories || [])}
          </section>`
        : ""
    }
  `;
}

function renderCertificateDetail(cert) {
  const el = document.getElementById("certDetail");
  el.className = "out history-detail is-ready";
  el.innerHTML = `
    <h3 class="report-title">${escapeHtml(cert.certificate_id)}</h3>
    <section class="report-section">
      <span class="report-label">Learner</span>
      <p class="report-copy"><strong>${escapeHtml(cert.learner_name)}</strong></p>
    </section>
    <section class="report-section">
      <span class="report-label">Lesson</span>
      <p class="report-copy">${escapeHtml(cert.lesson_title_en)}</p>
    </section>
    <section class="report-section">
      <span class="report-label">Issued</span>
      <p class="report-copy">${escapeHtml(cert.issued_on)} ù ${escapeHtml(cert.issuer)}</p>
    </section>
    <section class="report-section">
      <span class="report-label">Stored</span>
      <p class="report-copy">${escapeHtml(formatTime(cert.created_at))}</p>
    </section>
  `;
}

function renderHistoryList(checks) {
  const list = document.getElementById("historyList");
  const lead = document.getElementById("historyLead");

  if (!checks.length) {
    lead.textContent = "No stored checks yet. Run a verification from the home page.";
    list.innerHTML = "";
    return;
  }

  lead.textContent = `${checks.length} recent check${checks.length === 1 ? "" : "s"} stored on this deployment.`;
  list.innerHTML = checks
    .map(
      (check) => `
        <button type="button" class="history-item" data-check-id="${escapeHtml(check.id)}">
          <div class="history-item-top">
            <span class="band ${escapeHtml(check.risk_band || "low")}">${escapeHtml(String(check.check_type).toUpperCase())}</span>
            <span class="muted">#${escapeHtml(check.id)}</span>
          </div>
          <p class="history-item-title">${escapeHtml(checkSummaryInput(check))}</p>
          <p class="muted">${escapeHtml(formatTime(check.created_at))}</p>
        </button>
      `
    )
    .join("");

  list.querySelectorAll(".history-item").forEach((btn) => {
    btn.onclick = async () => {
      list.querySelectorAll(".history-item").forEach((item) => item.classList.remove("active"));
      btn.classList.add("active");
      const id = btn.getAttribute("data-check-id");
      const res = await fetch(`/api/v1/checks/${id}`);
      if (!res.ok) return;
      renderCheckDetail(await res.json());
    };
  });
}

function renderCertList(certificates) {
  const list = document.getElementById("certList");
  if (!certificates.length) {
    list.innerHTML = '<p class="report-copy muted">No certificates stored yet.</p>';
    return;
  }

  list.innerHTML = certificates
    .map(
      (cert) => `
        <button type="button" class="history-item" data-cert-id="${escapeHtml(cert.certificate_id)}">
          <div class="history-item-top">
            <strong>${escapeHtml(cert.certificate_id)}</strong>
          </div>
          <p class="history-item-title">${escapeHtml(cert.learner_name)}</p>
          <p class="muted">${escapeHtml(cert.lesson_title_en)}</p>
        </button>
      `
    )
    .join("");

  list.querySelectorAll(".history-item").forEach((btn) => {
    btn.onclick = async () => {
      const id = btn.getAttribute("data-cert-id");
      const res = await fetch(`/api/v1/certificates/${encodeURIComponent(id)}`);
      if (!res.ok) return;
      renderCertificateDetail(await res.json());
    };
  });
}

let activeType = "";

async function loadRecentChecks() {
  const list = document.getElementById("historyList");
  list.innerHTML = '<p class="report-copy muted">Loading...</p>';
  const query = activeType ? `?limit=20&check_type=${encodeURIComponent(activeType)}` : "?limit=20";
  const res = await fetch(`/api/v1/checks/recent${query}`);
  const data = await res.json();
  renderHistoryList(data.checks || []);
}

async function loadRecentCertificates() {
  const res = await fetch("/api/v1/certificates/recent?limit=10");
  const data = await res.json();
  renderCertList(data.certificates || []);
  if (data.certificates?.length) {
    renderCertificateDetail(data.certificates[0]);
  }
}

document.querySelectorAll(".filter-chip").forEach((chip) => {
  chip.onclick = () => {
    document.querySelectorAll(".filter-chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    activeType = chip.getAttribute("data-type") || "";
    loadRecentChecks();
  };
});

document.getElementById("refreshHistory").onclick = async () => {
  await Promise.all([loadRecentChecks(), loadRecentCertificates()]);
};

document.getElementById("lookupCert").onclick = async () => {
  const id = document.getElementById("certLookupId").value.trim();
  if (!id) return;
  const res = await fetch(`/api/v1/certificates/${encodeURIComponent(id)}`);
  const el = document.getElementById("certDetail");
  if (!res.ok) {
    el.className = "out history-detail";
    el.innerHTML = '<p class="report-copy">Certificate not found.</p>';
    return;
  }
  renderCertificateDetail(await res.json());
};

loadRecentChecks();
loadRecentCertificates();

async function openCheckFromQuery() {
  const params = new URLSearchParams(window.location.search);
  const checkId = params.get("check");
  if (!checkId) return;
  const res = await fetch(`/api/v1/checks/${encodeURIComponent(checkId)}`);
  if (!res.ok) return;
  const check = await res.json();
  renderCheckDetail(check);
  const btn = document.querySelector(`.history-item[data-check-id="${checkId}"]`);
  if (btn) btn.classList.add("active");
}

openCheckFromQuery();

async function loadProfileStatus() {
  const status = document.getElementById("profileStatus");
  const form = document.getElementById("profileForm");
  const userId = getUserId();
  if (!userId) return;

  const res = await fetch(`/api/v1/users/${encodeURIComponent(userId)}`);
  if (!res.ok) {
    localStorage.removeItem("mboashield_user_id");
    return;
  }

  const user = await res.json();
  status.textContent = `Signed in as ${user.display_name} (profile #${user.id}). Future checks will be linked to you.`;
  form.classList.add("hidden");
}

document.getElementById("profileForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const display_name = document.getElementById("profileName").value.trim();
  const email = document.getElementById("profileEmail").value.trim();
  if (!display_name) return;

  const res = await fetch("/api/v1/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ display_name, email: email || null }),
  });
  if (!res.ok) return;

  const user = await res.json();
  localStorage.setItem("mboashield_user_id", String(user.id));
  await loadProfileStatus();
});

loadProfileStatus();
