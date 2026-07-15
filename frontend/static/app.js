const i18n = {
  en: {
    textTitle: "1. Check a WhatsApp rumour",
    impTitle: "2. Check account impersonation",
    mediaTitle: "3. Check an image",
    ambTitle: "4. Mboa Ambassadors",
    langBtn: "FR",
  },
  fr: {
    textTitle: "1. Vérifier une rumeur WhatsApp",
    impTitle: "2. Vérifier une usurpation de compte",
    mediaTitle: "3. Vérifier une image",
    ambTitle: "4. Ambassadeurs Mboa",
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

function pretty(data) {
  return JSON.stringify(data, null, 2);
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
  document.getElementById("textOut").textContent = pretty(await res.json());
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
  document.getElementById("impOut").textContent = pretty(await res.json());
};

document.getElementById("checkMedia").onclick = async () => {
  const file = document.getElementById("mediaFile").files[0];
  if (!file) {
    document.getElementById("mediaOut").textContent = "Choose an image first.";
    return;
  }
  const fd = new FormData();
  fd.append("file", file);
  fd.append("lang", lang);
  const res = await fetch("/api/v1/check/media", { method: "POST", body: fd });
  document.getElementById("mediaOut").textContent = pretty(await res.json());
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
  el.innerHTML = `
    <h3>Certificate ${cert.id}</h3>
    <p>Awarded to <strong>${cert.learner_name}</strong></p>
    <p>${cert.lesson_title_en}</p>
    <p class="muted">${cert.issuer} · ${cert.issued_on}</p>
  `;
};

document.getElementById("runDemo").onclick = async () => {
  const status = document.getElementById("demoStatus");
  status.textContent = "Running scenario 1/3";
  document.getElementById("claimText").value =
    "URGENT!!! Le ministre annonce un couvre-feu national. Transfere plein de fois avant suppression. Envoie de l'argent au numero MoMo pour securiser ton compte.";
  await document.getElementById("checkText").onclick();

  status.textContent = "Running scenario 2/3";
  document.getElementById("impName").value = "MINPOSTEL Officiel Verifie";
  document.getElementById("impHandle").value = "@minpostel_cm_info";
  await document.getElementById("checkImp").onclick();

  status.textContent = "Running scenario 3/3";
  document.getElementById("learnerName").value = "Justene Nkwagoh Tamah";
  if (document.getElementById("lessonSelect").options.length) {
    document.getElementById("lessonSelect").selectedIndex = 0;
  }
  await document.getElementById("completeLesson").onclick();
  status.textContent = "Demo ready for pitch (text + impersonation + certificate). Upload any image for media.";
};

applyLang();
loadLessons();
