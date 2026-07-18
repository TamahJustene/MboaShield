async function loadHealth() {
  const el = document.getElementById("hubHealth");
  try {
    const [healthRes, progRes] = await Promise.all([
      fetch("/health"),
      fetch("/api/v1/program"),
    ]);
    const d = await healthRes.json();
    const version = document.getElementById("hubVersion");
    if (version) {
      version.textContent = `v${d.version} - MboaShield 2030 ${d.transformation_phase} - End-to-end`;
    }
    let progLine = "";
    if (progRes.ok) {
      const p = await progRes.json();
      progLine = `<p>Program <strong>${p.program}</strong> phase ${p.transformation_phase} - pack ${p.country_pack} - ${p.pillars.length} pillars</p>`;
    }
    el.className = "out history-detail is-ready";
    el.innerHTML = `
      <p><strong>${d.product}</strong> v${d.version} - ${d.deployment_profile}</p>
      ${progLine}
      <p>Engines ${d.ai_engine_version} - governance ${d.governance} - workers ${d.workers}</p>
    `;
  } catch (e) {
    el.textContent = "Could not load /health";
  }
}
loadHealth();
