/**
 * MboaShield portal shell (T3) - shared auth, nav, tenant, i18n FR/EN.
 * Mount: <div id="portal-shell" data-portal="analyst" data-title="..." data-tagline="..."></div>
 */
(function () {
  const STORAGE_LANG = "mboashield_lang";
  const STORAGE_TOKEN = "mboashield_access_token";

  const I18N = {
    en: {
      home: "Home",
      hub: "Hub",
      analyst: "Analyst",
      ntoc: "NTOC",
      institution: "Institution",
      developer: "Developers",
      intel: "Intel",
      investigation: "Investigation",
      national: "National",
      identity: "Sign in",
      signedIn: "Signed in",
      guest: "Guest (soft auth)",
      langBtn: "FR",
      tenant: "Tenant",
      docs: "API docs",
    },
    fr: {
      home: "Accueil",
      hub: "Hub",
      analyst: "Analyste",
      ntoc: "NTOC",
      institution: "Institution",
      developer: "Developpeurs",
      intel: "Intel",
      investigation: "Enquete",
      national: "National",
      identity: "Connexion",
      signedIn: "Connecte",
      guest: "Invite (auth souple)",
      langBtn: "EN",
      tenant: "Locataire",
      docs: "Docs API",
    },
  };

  const PORTALS = [
    { id: "analyst", href: "/static/analyst.html", labelKey: "analyst" },
    { id: "ntoc", href: "/static/ntoc.html", labelKey: "ntoc" },
    { id: "intel", href: "/static/intel.html", labelKey: "intel" },
    { id: "investigation", href: "/static/investigation.html", labelKey: "investigation" },
    { id: "national", href: "/static/national.html", labelKey: "national" },
    { id: "institution", href: "/static/institution-portal.html", labelKey: "institution" },
    { id: "developer", href: "/static/developer.html", labelKey: "developer" },
  ];

  function getLang() {
    const stored = localStorage.getItem(STORAGE_LANG);
    return stored === "fr" ? "fr" : "en";
  }

  function setLang(lang) {
    localStorage.setItem(STORAGE_LANG, lang === "fr" ? "fr" : "en");
  }

  function t(key) {
    const pack = I18N[getLang()] || I18N.en;
    return pack[key] || I18N.en[key] || key;
  }

  function getAccessToken() {
    return localStorage.getItem(STORAGE_TOKEN);
  }

  function authHeaders(extra) {
    const token = getAccessToken();
    const headers = Object.assign({}, extra || {});
    if (token) headers.Authorization = "Bearer " + token;
    return headers;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function mountTarget() {
    return document.getElementById("portal-shell");
  }

  function readMeta(el) {
    return {
      portal: (el && el.getAttribute("data-portal")) || "ops",
      title: (el && el.getAttribute("data-title")) || "MboaShield",
      tagline: (el && el.getAttribute("data-tagline")) || "",
      eyebrow: (el && el.getAttribute("data-eyebrow")) || "MboaShield 2030",
    };
  }

  async function loadContext() {
    const ctx = {
      version: "",
      tenant: "",
      tenantName: "",
      phase: "",
      countryPack: "",
    };
    try {
      const health = await fetch("/health").then((r) => r.json());
      ctx.version = health.version || "";
      ctx.tenant = health.tenant_id || "";
      ctx.phase = health.transformation_phase || "";
      ctx.countryPack = health.country_pack || "";
    } catch (_) {}
    try {
      const program = await fetch("/api/v1/program").then((r) => r.json());
      ctx.tenantName = program.tenant_display_name || "";
      ctx.phase = program.transformation_phase || ctx.phase;
      ctx.version = program.version || ctx.version;
    } catch (_) {}
    return ctx;
  }

  function renderShell(meta, ctx) {
    const el = mountTarget();
    if (!el) return;

    const active = meta.portal;
    const authLabel = getAccessToken() ? t("signedIn") : t("guest");
    const nav = PORTALS.map((item) => {
      const cls = item.id === active ? "btn-primary history-link" : "btn-ghost history-link";
      return `<a href="${item.href}" class="${cls}" data-shell-nav="${item.id}">${escapeHtml(t(item.labelKey))}</a>`;
    }).join("");

    el.innerHTML = `
      <header class="app-header portal-shell-header">
        <div class="brand">
          <p class="eyebrow">${escapeHtml(meta.eyebrow)} · v${escapeHtml(ctx.version || "?")} · ${escapeHtml(ctx.phase || "")}</p>
          <h1>${escapeHtml(meta.title)}</h1>
          <p class="tagline">${escapeHtml(meta.tagline)}</p>
          <p class="muted portal-shell-tenant">${escapeHtml(t("tenant"))}: ${escapeHtml(ctx.tenantName || ctx.tenant || "cm")} · pack ${escapeHtml(ctx.countryPack || "cm")}</p>
        </div>
        <div class="header-actions portal-shell-actions">
          <button type="button" id="portalLangToggle" class="btn-ghost">${escapeHtml(t("langBtn"))}</button>
          <a href="/static/identity.html" class="btn-ghost history-link">${escapeHtml(getAccessToken() ? t("signedIn") : t("identity"))}</a>
          <a href="/static/hub.html" class="btn-ghost history-link">${escapeHtml(t("hub"))}</a>
          <a href="/" class="btn-ghost history-link">${escapeHtml(t("home"))}</a>
        </div>
      </header>
      <nav class="portal-shell-nav" aria-label="Portal navigation">
        ${nav}
        <a href="/docs" class="btn-ghost history-link">${escapeHtml(t("docs"))}</a>
        <span class="muted portal-shell-auth">${escapeHtml(authLabel)}</span>
      </nav>
    `;

    const toggle = document.getElementById("portalLangToggle");
    if (toggle) {
      toggle.onclick = () => {
        setLang(getLang() === "en" ? "fr" : "en");
        boot();
      };
    }

    document.documentElement.lang = getLang();
  }

  async function boot() {
    const el = mountTarget();
    if (!el) return;
    const meta = readMeta(el);
    const ctx = await loadContext();
    renderShell(meta, ctx);
    document.dispatchEvent(new CustomEvent("mboashield:portal-ready", { detail: { meta, ctx, lang: getLang() } }));
  }

  window.MboaShieldPortal = {
    getLang,
    setLang,
    t,
    getAccessToken,
    authHeaders,
    boot,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
