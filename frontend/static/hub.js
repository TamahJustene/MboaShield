async function loadHealth() {
  const el = document.getElementById("hubHealth");
  try {
    const res = await fetch("/health");
    const d = await res.json();
    el.className = "out history-detail is-ready";
    el.innerHTML = `
      <p><strong>${d.product}</strong> v${d.version} · ${d.deployment_profile}</p>
      <p>Engines ${d.ai_engine_version} · governance ${d.governance} · advanced_ai ${d.advanced_ai} · workers ${d.workers}</p>
    `;
  } catch (e) {
    el.textContent = "Could not load /health";
  }
}
loadHealth();
