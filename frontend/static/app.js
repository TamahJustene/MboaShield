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

function applyLang() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    el.textContent = i18n[lang][key];
  });
  document.getElementById("langToggle").textContent = i18n[lang].langBtn;
}

function renderReport(targetId, data, extra = "") {
  const el = document.getElementById(targetId);
  const band = data.risk_band || "low";
  const score = data.risk_score ?? "-";
  const reasons = (data.reasons || []).map((r) => `- ${r}`).join("\n");
  const sources = (data.suggested_sources || [])
    .map((s) => `- ${s.title}: ${s.url}`)
    .join("\n");
  const matched = data.matched_institution
    ? `\nMatched institution: ${data.matched_institution.short_name} (${data.matched_institution.name})`
    : "";
  let verifyBlock = "";
  if (data.source_verification) {
    const v = data.source_verification;
    verifyBlock = `\n\n<strong>Source check:</strong> ${v.status}\n${v.summary}`;
    if (v.scam_signals?.length) {
      verifyBlock += `\nScam signals: ${v.scam_signals.join(", ")}`;
    }
  }
  el.innerHTML = `<span class="band ${band}">${String(band).toUpperCase()} · ${score}/100</span>\n` +
    `<strong>Advice:</strong> ${data.advice || ""}${matched}\n\n` +
    `<strong>Why:</strong>\n${reasons || "-"}` +
    (sources ? `\n\n<strong>Sources:</strong>\n${sources}` : "") +
    verifyBlock +
    (extra ? `\n\n${extra}` : "") +
    (data.meta ? `\n\n<strong>Meta:</strong>\n${JSON.stringify(data.meta, null, 2)}` : "");
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
  const res = await fetch("/api/v1/check/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, lang }),
  });
  renderReport("textOut", await res.json());
};

document.getElementById("checkImp").onclick = async () => {
  const res = await fetch("/api/v1/check/impersonation", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
  const fd = new FormData();
  fd.append("file", file);
  fd.append("lang", lang);
  const res = await fetch("/api/v1/check/audio", { method: "POST", body: fd });
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
  const fd = new FormData();
  fd.append("file", file);
  fd.append("lang", lang);
  const res = await fetch("/api/v1/check/media", { method: "POST", body: fd });
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
  const status = document.getElementById("demoStatus");
  status.textContent = "Running scenario 1/5...";
  document.getElementById("claimText").value =
    "URGENT!!! Le ministre annonce un couvre-feu national. Transferre plein de fois avant suppression. Envoie de l'argent au numero MoMo pour securiser ton compte.";
  await document.getElementById("checkText").onclick();

  status.textContent = "Running scenario 2/5...";
  document.getElementById("impName").value = "MINPOSTEL Officiel Verifie";
  document.getElementById("impHandle").value = "@minpostel_cm_info";
  await document.getElementById("checkImp").onclick();

  status.textContent = "Running scenario 3/5...";
  await document.querySelector('.audio-sample[data-sample="/static/samples/minister_voice_clone.wav"]').onclick();

  status.textContent = "Running scenario 4/5...";
  await document.querySelector('.sample[data-sample="/static/samples/synthetic_smooth_face.jpg"]').onclick();

  status.textContent = "Running scenario 5/5...";
  document.getElementById("learnerName").value = "Justene Nkwagoh Tamah";
  if (document.getElementById("lessonSelect").options.length) {
    document.getElementById("lessonSelect").selectedIndex = 0;
  }
  await document.getElementById("completeLesson").onclick();
  status.textContent = "Demo complete: text + impersonation + audio + image + certificate.";
};

document.querySelectorAll(".nav-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const target = chip.getAttribute("data-target");
    document.querySelectorAll(".nav-chip").forEach((c) => c.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    chip.classList.add("active");
    const panel = document.getElementById(target);
    if (panel) {
      panel.classList.add("active");
      panel.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});

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
  el.innerHTML = `
    <h3>Certificate ${cert.id}</h3>
    <p>Awarded to <strong>${cert.learner_name}</strong></p>
    <p>${cert.lesson_title_en}</p>
    <p class="muted">${cert.issuer} - ${cert.issued_on}</p>
  `;
};

applyLang();
loadLessons();
