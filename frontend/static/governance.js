async function loadHealth() {
  const res = await fetch("/api/v1/governance/health");
  const data = await res.json();
  const el = document.getElementById("govHealth");
  if (!res.ok) {
    el.textContent = data.detail || "Governance unavailable";
    return;
  }
  el.className = "out history-detail is-ready";
  el.innerHTML = `
    <p>Risks: <strong>${data.risks}</strong> | Controls: <strong>${data.controls}</strong></p>
    <p>Model cards: ${data.model_cards} | Dataset cards: ${data.dataset_cards}</p>
    <p>Certainty policy: <strong>${data.certainty_policy}</strong></p>
  `;
}

async function loadCompliance() {
  const res = await fetch("/api/v1/governance/compliance");
  const data = await res.json();
  document.getElementById("complianceOut").textContent = res.ok
    ? JSON.stringify(
        {
          risks_open: data.risks_open,
          risks_total: data.risks_total,
          controls_implemented: data.controls_implemented,
          controls_total: data.controls_total,
          certainty_policy: data.certainty_policy,
        },
        null,
        2
      )
    : JSON.stringify(data, null, 2);
}

async function loadRisks() {
  const res = await fetch("/api/v1/governance/risks");
  const data = await res.json();
  document.getElementById("risksOut").textContent = res.ok
    ? (data.items || [])
        .map((r) => `${r.risk_id} [${r.status}] ${r.title} -> ${r.threat_model_ref}`)
        .join("\n")
    : JSON.stringify(data, null, 2);
}

async function loadCards() {
  const res = await fetch("/api/v1/governance/model-cards");
  const data = await res.json();
  document.getElementById("cardsOut").textContent = res.ok
    ? (data.items || [])
        .map((c) => `${c.card_id}: ${c.title} (certainty=${c.certainty_policy})`)
        .join("\n")
    : JSON.stringify(data, null, 2);
}

async function setConsent(granted) {
  const subject_key = document.getElementById("subjectKey").value.trim();
  const feature = document.getElementById("featureSelect").value;
  const res = await fetch("/api/v1/governance/consent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ subject_key, feature, granted }),
  });
  const data = await res.json();
  document.getElementById("consentOut").textContent = JSON.stringify(data, null, 2);
}

document.getElementById("grantBtn").onclick = () => setConsent(true);
document.getElementById("revokeBtn").onclick = () => setConsent(false);
loadHealth();
loadCompliance();
loadRisks();
loadCards();
