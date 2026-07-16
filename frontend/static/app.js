const i18n = {
  en: {
    textTitle: "1. Check a WhatsApp rumour",
    impTitle: "2. Check account impersonation",
    audioTitle: "3. Check a voice note (clone risk)",
    mediaTitle: "4. Check an image",
    ambTitle: "5. Mboa Ambassadors",
    langBtn: "FR",
  },
  fr: {
    textTitle: "1. Verifier une rumeur WhatsApp",
    impTitle: "2. Verifier une usurpation de compte",
    audioTitle: "3. Verifier une note vocale (clone)",
    mediaTitle: "4. Verifier une image",
    ambTitle: "5. Ambassadeurs Mboa",
    langBtn: "EN",
  },
};

let lang = "en";
const demoSummary = [];
let demoRunning = false;

function getUserId() {
  return localStorage.getItem("mboashield_user_id");
}

function userHeaders(extra = {}) {
  const userId = getUserId();
  return userId ? { ...extra, "X-MboaShield-User-Id": userId } : extra;
}

const panelMeta = {
  textOut: {
    title: "Rumour risk",
    proof: "This proves MboaShield can slow down panic before a citizen forwards a dangerous message.",
    action: "Do not forward. Cross-check with trusted public sources first.",
  },
  impOut: {
    title: "Identity protection",
    proof: "This proves fake institutional accounts can be challenged before they harvest trust or money.",
    action: "Trust only verified institutional handles and public directories.",
  },
  audioOut: {
    title: "Voice-clone detection",
    proof: "This proves cloned authority voices can be treated as suspicious instead of instantly obeyed.",
    action: "Call back via an official number before acting on audio instructions.",
  },
  mediaOut: {
    title: "Image integrity",
    proof: "This proves suspicious visuals can be explained in plain language, not only by a technical score.",
    action: "Ask for original source context before sharing emotionally loaded images.",
  },
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function showLoading(targetId, message) {
  const el = document.getElementById(targetId);
  el.className = "out is-loading";
  el.innerHTML = `
    <p class="loading-row">
      <span class="loading-dot" aria-hidden="true"></span>
      <span class="loading-dot" aria-hidden="true"></span>
      <span class="loading-dot" aria-hidden="true"></span>
      <span>${escapeHtml(message)}</span>
    </p>
  `;
}

function setDemoProgress(step, total = 5) {
  const wrap = document.getElementById("demoProgress");
  const bar = document.getElementById("demoProgressBar");
  const label = document.getElementById("demoProgressLabel");
  wrap.classList.remove("hidden");
  wrap.setAttribute("aria-hidden", "false");
  const pct = Math.round((step / total) * 100);
  bar.style.width = `${pct}%`;
  label.textContent = `${step} / ${total} scenarios`;
}

function markChecklist(step, state) {
  document.querySelectorAll("#demoChecklist li").forEach((li) => {
    const n = Number(li.getAttribute("data-step"));
    li.classList.remove("active", "done");
    if (n < step) li.classList.add("done");
    if (n === step && state === "active") li.classList.add("active");
    if (n === step && state === "done") li.classList.add("done");
  });
}

function hideJuryFinale() {
  const el = document.getElementById("juryFinale");
  el.classList.add("hidden");
}

function showJuryFinale() {
  const el = document.getElementById("juryFinale");
  el.classList.remove("hidden");
  el.scrollIntoView({ behavior: "smooth", block: "start" });
}

function setDemoRunning(running) {
  demoRunning = running;
  const btn = document.getElementById("runDemo");
  btn.disabled = running;
  document.getElementById("demoStatus").classList.toggle("is-running", running);
}

function activatePanel(panelId, focus = false) {
  document.querySelectorAll(".nav-chip").forEach((c) => {
    c.classList.toggle("active", c.getAttribute("data-target") === panelId);
  });
  document.querySelectorAll(".panel").forEach((p) => {
    p.classList.toggle("active", p.id === panelId);
    p.classList.toggle("demo-focus", focus && p.id === panelId);
  });
  const panel = document.getElementById(panelId);
  if (panel) {
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function listHtml(items) {
  if (!items || !items.length) {
    return '<p class="report-copy">-</p>';
  }
  return `<ul class="report-list">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function renderSummary() {
  const lead = document.getElementById("summaryLead");
  const cards = document.getElementById("summaryCards");
  if (!demoSummary.length) {
    lead.textContent = "Run the 90s demo to generate a final protection summary for the judges.";
    cards.innerHTML = "";
    return;
  }

  lead.textContent = "MboaShield protected one citizen journey across misinformation, impersonation, synthetic media, and civic education.";
  cards.innerHTML = demoSummary
    .map(
      (item) => `
        <article class="summary-card">
          <span class="band ${escapeHtml(item.band)}">${escapeHtml(String(item.band).toUpperCase())}</span>
          <h3>${escapeHtml(item.title)}</h3>
          <p>${escapeHtml(item.summary)}</p>
        </article>
      `
    )
    .join("");
}

function applyLang() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    el.textContent = i18n[lang][key];
  });
  document.getElementById("langToggle").textContent = i18n[lang].langBtn;
}

function renderReport(targetId, data, extra = "") {
  const el = document.getElementById(targetId);
  const meta = panelMeta[targetId] || {};
  const band = data.risk_band || "low";
  const score = data.risk_score ?? "-";
  const reasons = data.reasons || [];
  const sources = (data.suggested_sources || []).map((s) => `${s.title}: ${s.url}`);
  const matched = data.matched_institution
    ? `${data.matched_institution.short_name} (${data.matched_institution.name})`
    : "";
  let verifyBlock = "";
  if (data.source_verification) {
    const v = data.source_verification;
    verifyBlock = `
      <section class="report-section">
        <span class="report-label">Source check</span>
        <p class="report-copy"><strong>${escapeHtml(v.status)}</strong> - ${escapeHtml(v.summary || "")}</p>
        ${
          v.scam_signals?.length
            ? `<p class="report-copy"><strong>Scam signals:</strong> ${escapeHtml(v.scam_signals.join(", "))}</p>`
            : ""
        }
      </section>
    `;
  }

  el.className = "out is-ready";
  el.innerHTML = `
    <span class="band ${escapeHtml(band)}">${escapeHtml(String(band).toUpperCase())} · ${escapeHtml(score)}/100</span>
    <h3 class="report-title">${escapeHtml(meta.title || "Risk report")}</h3>
    ${meta.proof ? `<p class="proof">${escapeHtml(meta.proof)}</p>` : ""}
    <section class="report-section">
      <span class="report-label">Recommended action</span>
      <p class="report-copy">${escapeHtml(data.advice || meta.action || "")}</p>
    </section>
    ${
      matched
        ? `<section class="report-section"><span class="report-label">Matched institution</span><p class="report-copy">${escapeHtml(matched)}</p></section>`
        : ""
    }
    <section class="report-section">
      <span class="report-label">Why it was flagged</span>
      ${listHtml(reasons)}
    </section>
    ${
      sources.length
        ? `<section class="report-section"><span class="report-label">Trusted sources</span>${listHtml(sources)}</section>`
        : ""
    }
    ${verifyBlock}
    ${
      data.ai_analysis
        ? `<section class="report-section ai-block">
            <span class="report-label">AI analysis</span>
            <p class="report-copy"><strong>${escapeHtml(data.ai_analysis.narrative || "")}</strong></p>
            <p class="report-copy muted">Confidence ${escapeHtml(data.ai_analysis.confidence ?? "-")}/100 · Engine ${escapeHtml(data.ai_analysis.engine_version || "")}</p>
            ${
              (data.ai_analysis.threat_categories || []).length
                ? `<p class="report-copy"><strong>Threats:</strong> ${escapeHtml((data.ai_analysis.threat_categories || []).join(", "))}</p>`
                : ""
            }
            ${
              data.nlp
                ? `<p class="report-copy muted">NLP engine ${escapeHtml(data.nlp.engine_version || "")} · probability ${escapeHtml(data.nlp.probability ?? "-")}</p>`
                : ""
            }
            ${
              data.backend
                ? `<p class="report-copy muted">Detector backend: ${escapeHtml(data.backend)}${data.engine ? ` · ${escapeHtml(data.engine)}` : ""}</p>`
                : ""
            }
            ${listHtml(data.ai_analysis.next_actions || [])}
          </section>`
        : ""
    }
    ${
      extra
        ? `<section class="report-section summary-note">${extra}</section>`
        : ""
    }
    ${
      data.check_id
        ? `<section class="report-section summary-note">
            <a href="/static/history.html?check=${escapeHtml(data.check_id)}">View stored check #${escapeHtml(data.check_id)}</a>
            ·
            <a href="/static/reports.html?check=${escapeHtml(data.check_id)}">Report incident</a>
          </section>`
        : ""
    }
  `;

  demoSummary.push({
    title: meta.title || targetId,
    band,
    summary: data.advice || meta.action || "Action recommended.",
  });
  renderSummary();
}

async function loadLessons() {
  const res = await fetch("/api/v1/ambassadors/lessons");
  const data = await res.json();
  const box = document.getElementById("lessons");
  const select = document.getElementById("lessonSelect");
  box.innerHTML = "";
  select.innerHTML = "";
  data.lessons.forEach((lesson) => {
    const div = document.createElement("div");
    div.className = "lesson";
    const title = lang === "fr" ? lesson.title_fr : lesson.title_en;
    div.innerHTML = `<strong>${title}</strong><div class="muted">${lesson.minutes} min</div>`;
    box.appendChild(div);
    const opt = document.createElement("option");
    opt.value = lesson.id;
    opt.textContent = title;
    select.appendChild(opt);
  });
}

document.getElementById("langToggle").onclick = async () => {
  lang = lang === "en" ? "fr" : "en";
  applyLang();
  await loadLessons();
};

document.getElementById("checkText").onclick = async () => {
  const text = document.getElementById("claimText").value;
  showLoading("textOut", "Analysing rumour and checking trusted sources...");
  const res = await fetch("/api/v1/check/text", {
    method: "POST",
    headers: userHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ text, lang }),
  });
  renderReport("textOut", await res.json());
};

document.getElementById("checkImp").onclick = async () => {
  showLoading("impOut", "Checking identity signals against the institution registry...");
  const res = await fetch("/api/v1/check/impersonation", {
    method: "POST",
    headers: userHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      name: document.getElementById("impName").value,
      handle: document.getElementById("impHandle").value,
      lang,
    }),
  });
  renderReport("impOut", await res.json());
};

async function analyseAudioFile(file) {
  if (!file) {
    document.getElementById("audioOut").textContent = "Choose an audio file first (or click sample).";
    return;
  }
  showLoading("audioOut", "Listening for cloned-voice risk patterns...");
  const fd = new FormData();
  fd.append("file", file);
  fd.append("lang", lang);
  const res = await fetch("/api/v1/check/audio", { method: "POST", headers: userHeaders(), body: fd });
  renderReport("audioOut", await res.json());
}

document.getElementById("checkAudio").onclick = async () => {
  await analyseAudioFile(document.getElementById("audioFile").files[0]);
};

document.querySelectorAll(".audio-sample").forEach((btn) => {
  btn.onclick = async () => {
    const url = btn.getAttribute("data-sample");
    const blob = await fetch(url).then((r) => r.blob());
    const file = new File([blob], url.split("/").pop(), { type: "audio/wav" });
    const dt = new DataTransfer();
    dt.items.add(file);
    document.getElementById("audioFile").files = dt.files;
    await analyseAudioFile(file);
  };
});

document.getElementById("checkMedia").onclick = async () => {
  const file = document.getElementById("mediaFile").files[0];
  if (!file) {
    document.getElementById("mediaOut").textContent = "Choose an image first (or click a sample).";
    return;
  }
  showLoading("mediaOut", "Inspecting image integrity and synthetic-media signals...");
  const fd = new FormData();
  fd.append("file", file);
  fd.append("lang", lang);
  const res = await fetch("/api/v1/check/media", { method: "POST", headers: userHeaders(), body: fd });
  renderReport("mediaOut", await res.json());
};

document.querySelectorAll(".sample").forEach((btn) => {
  btn.onclick = async () => {
    const url = btn.getAttribute("data-sample");
    const blob = await fetch(url).then((r) => r.blob());
    const file = new File([blob], url.split("/").pop(), { type: blob.type || "image/jpeg" });
    const dt = new DataTransfer();
    dt.items.add(file);
    document.getElementById("mediaFile").files = dt.files;
    await document.getElementById("checkMedia").onclick();
  };
});

document.getElementById("runDemo").onclick = async () => {
  if (demoRunning) return;
  const status = document.getElementById("demoStatus");
  setDemoRunning(true);
  hideJuryFinale();
  demoSummary.length = 0;
  renderSummary();
  document.getElementById("cert").classList.add("hidden");
  document.querySelectorAll(".panel").forEach((p) => p.classList.remove("demo-focus"));
  setDemoProgress(0);

  activatePanel("panel-text", true);
  markChecklist(1, "active");
  status.textContent = "Grand Jury mode: scenario 1/5 - stopping a WhatsApp rumour before it spreads.";
  document.getElementById("claimText").value =
    "URGENT!!! Le ministre annonce un couvre-feu national. Transferre plein de fois avant suppression. Envoie de l'argent au numero MoMo pour securiser ton compte.";
  await document.getElementById("checkText").onclick();
  setDemoProgress(1);
  markChecklist(1, "done");
  await sleep(700);

  activatePanel("panel-imp", true);
  markChecklist(2, "active");
  status.textContent = "Grand Jury mode: scenario 2/5 - exposing a fake public institution account.";
  document.getElementById("impName").value = "MINPOSTEL Officiel Verifie";
  document.getElementById("impHandle").value = "@minpostel_cm_info";
  await document.getElementById("checkImp").onclick();
  setDemoProgress(2);
  markChecklist(2, "done");
  await sleep(700);

  activatePanel("panel-audio", true);
  markChecklist(3, "active");
  status.textContent = "Grand Jury mode: scenario 3/5 - checking a suspicious authority voice note.";
  await document.querySelector('.audio-sample[data-sample="/static/samples/minister_voice_clone.wav"]').onclick();
  setDemoProgress(3);
  markChecklist(3, "done");
  await sleep(700);

  activatePanel("panel-media", true);
  markChecklist(4, "active");
  status.textContent = "Grand Jury mode: scenario 4/5 - explaining synthetic signals in an image.";
  await document.querySelector('.sample[data-sample="/static/samples/synthetic_smooth_face.jpg"]').onclick();
  setDemoProgress(4);
  markChecklist(4, "done");
  await sleep(700);

  activatePanel("panel-amb", true);
  markChecklist(5, "active");
  status.textContent = "Grand Jury mode: scenario 5/5 - turning awareness into digital patriotism.";
  document.getElementById("learnerName").value = "Justene Nkwagoh Tamah";
  if (document.getElementById("lessonSelect").options.length) {
    document.getElementById("lessonSelect").selectedIndex = 0;
  }
  await document.getElementById("completeLesson").onclick();
  setDemoProgress(5);
  markChecklist(5, "done");
  document.querySelectorAll(".panel").forEach((p) => p.classList.remove("demo-focus"));

  status.textContent = "Demo complete: one citizen protected across 5 AI threat scenarios.";
  status.classList.remove("is-running");
  setDemoRunning(false);
  await sleep(400);
  showJuryFinale();
};

document.getElementById("replayDemo").onclick = () => {
  document.getElementById("runDemo").scrollIntoView({ behavior: "smooth", block: "center" });
  document.getElementById("runDemo").click();
};

document.querySelectorAll(".nav-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    activatePanel(chip.getAttribute("data-target"));
  });
});

document.getElementById("runCaseAnalyze").onclick = async () => {
  const text = document.getElementById("caseText").value;
  const name = document.getElementById("caseName").value;
  const handle = document.getElementById("caseHandle").value;
  showLoading("caseOut", "Running multi-signal AI case analysis...");
  const res = await fetch("/api/v1/analyze", {
    method: "POST",
    headers: userHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ text, name, handle, lang }),
  });
  const data = await res.json();
  if (!res.ok) {
    document.getElementById("caseOut").className = "out";
    document.getElementById("caseOut").innerHTML = `<p class="report-copy">${escapeHtml(data.detail || "Analysis failed")}</p>`;
    return;
  }

  const overall = data.overall || {};
  const modules = data.modules || [];
  document.getElementById("caseOut").className = "out is-ready";
  document.getElementById("caseOut").innerHTML = `
    <span class="band ${escapeHtml(overall.risk_band || "low")}">${escapeHtml(String(overall.risk_band || "low").toUpperCase())} · ${escapeHtml(overall.risk_score ?? "-")}/100</span>
    <h3 class="report-title">AI case assessment</h3>
    <p class="proof">${escapeHtml(overall.narrative || "")}</p>
    <section class="report-section">
      <span class="report-label">Confidence</span>
      <p class="report-copy">${escapeHtml(overall.confidence ?? "-")}/100 · ${escapeHtml(overall.engine || "")} ${escapeHtml(overall.engine_version || "")}</p>
    </section>
    <section class="report-section">
      <span class="report-label">Threat categories</span>
      ${listHtml(overall.threat_categories || [])}
    </section>
    <section class="report-section">
      <span class="report-label">Next actions</span>
      ${listHtml(overall.next_actions || [])}
    </section>
    <section class="report-section">
      <span class="report-label">Modules analysed</span>
      ${listHtml(modules.map((m) => `${m.modality}: ${m.result?.risk_band || "-"} (${m.result?.risk_score ?? "-"}/100)`))}
    </section>
    ${
      data.case_check_id
        ? `<section class="report-section summary-note"><a href="/static/history.html?check=${escapeHtml(data.case_check_id)}">View stored case check #${escapeHtml(data.case_check_id)}</a></section>`
        : ""
    }
  `;
};

document.getElementById("completeLesson").onclick = async () => {
  const res = await fetch("/api/v1/ambassadors/complete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      lesson_id: document.getElementById("lessonSelect").value,
      learner_name: document.getElementById("learnerName").value,
    }),
  });
  const data = await res.json();
  const cert = data.certificate;
  const el = document.getElementById("cert");
  el.classList.remove("hidden");
  el.classList.add("cert-reveal");
  el.innerHTML = `
    <h3>Certificate ${cert.id}</h3>
    <p>Awarded to <strong>${cert.learner_name}</strong></p>
    <p>${cert.lesson_title_en}</p>
    <p class="muted">${cert.issuer} - ${cert.issued_on}</p>
  `;
  demoSummary.push({
    title: "Digital patriotism outcome",
    band: "low",
    summary: "The citizen finishes informed, certified, and less likely to spread harmful AI-generated content.",
  });
  renderSummary();
};

applyLang();
loadLessons();
