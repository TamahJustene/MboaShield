async function loadHealth() {
  const res = await fetch("/api/v1/ai-platform/health");
  const data = await res.json();
  const el = document.getElementById("aiHealth");
  if (!res.ok) {
    el.textContent = data.detail || "AI platform unavailable";
    return;
  }
  el.className = "out history-detail is-ready";
  el.innerHTML = `
    <p>Engine package <strong>${data.engine_package_version}</strong></p>
    <p>Models registered: ${data.models}</p>
    <p>Calibration samples: ${data.calibration?.samples ?? 0} (certainty: none)</p>
  `;
}

async function runEval(dataset) {
  const out = document.getElementById("evalOut");
  out.textContent = "Running...";
  const res = await fetch("/api/v1/ai-platform/evaluation/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset }),
  });
  const data = await res.json();
  out.textContent = res.ok ? JSON.stringify(data.metrics, null, 2) : JSON.stringify(data, null, 2);
}

document.getElementById("runEvalEn").onclick = () => runEval("en");
document.getElementById("runEvalFr").onclick = () => runEval("fr");
loadHealth();
