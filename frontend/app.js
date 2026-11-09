// ============================================================================
// AI Assisted Software Architecting Council — Frontend Controller (Clean UI)
// ============================================================================

const state = {
  scenarios: [],
  agents: [],
  kbItems: [],
  docs: [],
  currentSession: null,
  seenMessageIds: new Set(),
};

// Tab navigation
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    const pane = document.getElementById(btn.dataset.tab);
    if (pane) pane.classList.add("active");
  });
});

// Phase Stepper Highlighter
const PHASE_ORDER = ["FRAME", "PROPOSE", "CRITIQUE", "CONVERGE", "DECIDE"];
function highlightPhase(activePhase) {
  const idx = PHASE_ORDER.indexOf(activePhase);
  document.querySelectorAll("#phaseStepper .phase-step").forEach((el) => {
    const p = el.dataset.phase;
    const pIdx = PHASE_ORDER.indexOf(p);
    el.classList.remove("active", "done");
    if (p === activePhase) {
      el.classList.add("active");
    } else if (idx > -1 && pIdx < idx) {
      el.classList.add("done");
    }
  });
}

// Connect Server-Sent Events (SSE) for real-time A2A Message Bus observability
function connectSSE() {
  const pill = document.getElementById("sseStatusPill");
  const es = new EventSource("/api/stream");
  es.onopen = () => {
    pill.textContent = "● Canale Live Attivo";
    pill.classList.add("ok");
  };
  es.onmessage = (evt) => {
    try {
      const payload = JSON.parse(evt.data);
      if (payload.event === "phase_status") {
        highlightPhase(payload.phase);
        const badge = document.getElementById("debateStatusBadge");
        if (badge) badge.textContent = `${payload.phase}: ${payload.detail}`;
      } else if (payload.event === "a2a_message") {
        appendLiveMessage(payload.data);
      }
    } catch (e) {
      console.error("SSE parse error:", e);
    }
  };
  es.onerror = () => {
    pill.textContent = "○ Riconnessione...";
  };
}

const PHASE_LABELS_IT = {
  FRAME: "Fase 1: Inquadramento",
  PROPOSE: "Fase 2: Proposta Isolata",
  CRITIQUE: "Fase 3: Critica & Dibattito",
  CONVERGE: "Fase 4: Votazione",
  DECIDE: "Fase 5: Decisione ADR",
  HUMAN_FEEDBACK: "Intervento Architetto Umano",
};

// Render a single A2A message card in the Live Debate Stream
function appendLiveMessage(msg) {
  if (!msg || state.seenMessageIds.has(msg.message_id)) return;
  state.seenMessageIds.add(msg.message_id);

  highlightPhase(msg.phase);
  const stream = document.getElementById("debateStream");
  if (stream.querySelector(".placeholder-msg")) {
    stream.innerHTML = "";
  }

  const card = document.createElement("div");
  card.className = "msg-card";
  if (msg.sender_role === "chair") card.classList.add("chair");
  if (msg.sender_role === "human_architect") card.classList.add("human");

  const contract = msg.contract;
  let citationsHtml = "";
  if (contract && contract.citations && contract.citations.length > 0) {
    citationsHtml = contract.citations
      .map((cid) => `<span class="badge cite" title="Fonte citata dalla Knowledge Base">📚 ${cid}</span>`)
      .join(" ");
  }

  let mindChangedBadge = "";
  if (contract && contract.mind_changed) {
    mindChangedBadge = `<span class="badge changed">🔄 Ha cambiato idea: ${contract.change_reason || "Convinto dalle prove dei colleghi"}</span>`;
  }

  let choiceBannerHtml = "";
  if (contract && contract.selected_option) {
    choiceBannerHtml = `
      <div class="choice-banner">
        💡 <strong>Opzione Votata:</strong> <span style="color:var(--primary);font-weight:700;">${contract.selected_option}</span>
        <span style="float:right;font-size:0.8rem;color:var(--muted);">Sicurezza: <strong>${Math.round(contract.confidence * 100)}%</strong></span>
      </div>
    `;
  }

  let tradeoffsHtml = "";
  if (contract && contract.tradeoffs && Object.keys(contract.tradeoffs).length > 0) {
    const items = Object.entries(contract.tradeoffs)
      .map(([k, v]) => `<li><strong>${k}:</strong> ${v}</li>`)
      .join("");
    tradeoffsHtml = `
      <div style="margin-top:8px;background:var(--surface);padding:8px 12px;border-radius:8px;border:1px solid var(--line);">
        <strong style="font-size:0.78rem;color:var(--muted);">⚖ Compromessi (Trade-off) analizzati:</strong>
        <ul style="margin-top:4px;padding-left:18px;font-size:0.82rem;color:var(--muted);">${items}</ul>
      </div>`;
  }

  const phaseLabel = PHASE_LABELS_IT[msg.phase] || msg.phase;

  card.innerHTML = `
    <div class="msg-header">
      <div class="msg-sender">
        <span>${msg.sender_name}</span>
        <span class="badge stance">Carattere: ${msg.sender_stance}</span>
        <span class="badge">AI: ${msg.llm_family}</span>
        ${mindChangedBadge}
      </div>
      <span class="badge">${phaseLabel}</span>
    </div>
    ${choiceBannerHtml}
    <div class="msg-body">${formatMarkdownInline(msg.content)}</div>
    ${tradeoffsHtml}
    <div class="msg-meta">
      ${citationsHtml ? `<span>Fonti citate: ${citationsHtml}</span>` : ""}
      <span style="margin-left:auto;">Modello: <code>${msg.llm_model}</code> (${msg.latency_ms}ms)</span>
    </div>
  `;

  stream.appendChild(card);
  stream.scrollTop = stream.scrollHeight;
}

function formatMarkdownInline(text) {
  if (!text) return "";
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br/>");
}

// Render Synthesized ADR Proposal + Minority Dissent
function renderADR(session) {
  const container = document.getElementById("adrContainer");
  if (!session || !session.adr) {
    container.style.display = "none";
    return;
  }
  const adr = session.adr;
  container.style.display = "block";

  const votesHtml = Object.entries(adr.vote_breakdown || {})
    .map(([agent, opt]) => `<li style="margin-bottom:4px;"><strong>${agent}:</strong> ${opt}</li>`)
    .join("");

  const dissentHtml =
    adr.minority_dissent && adr.minority_dissent.length > 0
      ? adr.minority_dissent
          .map(
            (d) => `
          <div class="dissent-card">
            <strong>⚠️ Opinione Contraria (Minoranza) — ${d.agent_name} (${d.stance})</strong><br/>
            Voleva scegliere: <strong>${d.preferred_option}</strong><br/>
            Motivazione: ${d.rationale}
            <div style="margin-top:4px;font-size:0.78rem;">Fonti citate: ${(d.citations || []).map((c) => `[${c}]`).join(", ")}</div>
          </div>`
          )
          .join("")
      : `<div style="margin-top:8px;padding:10px;background:var(--green-soft);border:1px solid var(--green-border);border-radius:8px;font-size:0.86rem;color:#15803d;font-weight:600;">✓ Consenso Unanime! Tutti i 4 agenti sono d'accordo (0 Dissensi).</div>`;

  const madrOptionsHtml = (adr.options_analysis || [])
    .map(
      (oa) => `
      <div style="background:var(--surface-alt);padding:10px 12px;border-radius:8px;margin-top:8px;border:1px solid var(--line);border-left:4px solid ${oa.is_chosen ? "#16a34a" : "#94a3b8"};">
        <div style="font-size:0.88rem;font-weight:800;color:${oa.is_chosen ? "#15803d" : "var(--ink)"};">
          ${oa.is_chosen ? "✅ OPZIONE SCELTA: " : "❌ OPZIONE SCARTATA: "}${oa.option_name}
        </div>
        <div style="font-size:0.82rem;color:#15803d;margin-top:4px;"><strong>👍 Pro:</strong> ${(oa.pros || []).join("; ")}</div>
        <div style="font-size:0.82rem;color:#dc2626;margin-top:2px;"><strong>👎 Contro:</strong> ${(oa.cons || []).join("; ")}</div>
      </div>`
    )
    .join("");

  const gateBadge = adr.validation_gate_passed
    ? `<span class="pill ok">✓ Controllo Vincoli Superato</span>`
    : `<span class="pill" style="color:#dc2626;">⚠ Vincoli Corretti</span>`;

  container.innerHTML = `
    <div class="adr-box">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid var(--line);">
        <div>
          <span class="step-badge green">RISULTATO FINALE DEL CONSIGLIO (Verbale MADR)</span>
          <h3 style="font-size:1.25rem;font-weight:800;color:var(--ink);margin-top:4px;">${adr.adr_id}: ${adr.title}</h3>
        </div>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
          ${gateBadge}
          <span class="pill accent">Consenso: ${Math.round(adr.consensus_score * 100)}% (${adr.consensus_type})</span>
        </div>
      </div>

      <div style="background:var(--green-soft);border:1px solid var(--green-border);padding:14px 16px;border-radius:10px;margin-bottom:14px;">
        <div style="font-size:0.8rem;font-weight:700;color:#15803d;text-transform:uppercase;">Soluzione Tecnologica Proposta dal Consiglio:</div>
        <div style="font-size:1.15rem;font-weight:800;color:#14532d;margin-top:2px;">🏆 ${adr.chosen_option}</div>
        <p style="font-size:0.88rem;color:var(--ink);margin-top:8px;">${formatMarkdownInline(adr.rationale)}</p>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:12px;">
        <div style="background:var(--surface-alt);padding:12px 14px;border-radius:8px;border:1px solid var(--line);">
          <strong style="font-size:0.85rem;color:var(--ink);">🗳 Come hanno votato i 4 Agenti:</strong>
          <ul style="padding-left:18px;margin-top:6px;font-size:0.84rem;color:var(--muted);">${votesHtml}</ul>
        </div>
        <div style="background:var(--surface-alt);padding:12px 14px;border-radius:8px;border:1px solid var(--line);">
          <strong style="font-size:0.85rem;color:var(--ink);">🎯 Qualità ISO 25010 &amp; Fonti Citate:</strong>
          <p style="font-size:0.82rem;color:var(--muted);margin-top:6px;">
            <strong>Drivers:</strong> ${(adr.decision_drivers || []).join(" • ")}
          </p>
          <p style="margin-top:8px;font-size:0.82rem;color:var(--purple);font-weight:700;">
            📚 Prove Citate: ${(adr.citations || []).map((c) => `[${c}]`).join(", ")}
          </p>
        </div>
      </div>

      <div style="margin-top:16px;">
        <strong style="font-size:0.9rem;color:var(--ink);">📋 Analisi Pro &amp; Contro di Tutte le Opzioni (Standard MADR):</strong>
        ${madrOptionsHtml}
      </div>

      <div style="margin-top:16px;">
        <strong style="font-size:0.9rem;color:var(--ink);">📢 Registro delle Opinioni di Minoranza (Dissent):</strong>
        ${dissentHtml}
      </div>

      <div style="margin-top:16px;padding:12px;background:var(--primary-soft);border-radius:8px;border:1px solid #bfdbfe;font-size:0.86rem;color:var(--primary);">
        👉 <strong>Cosa fare adesso?</strong> Guarda a sinistra nel riquadro <strong>PASSO 3</strong>: puoi chiedere una modifica al volo (<strong>Opzione 3A</strong>) oppure approvare la decisione finale con il bottone verde (<strong>Opzione 3B</strong>)!
      </div>
    </div>
  `;

  // Populate Long-Loop dropdown with candidate options, defaulting to council's chosen option
  const llSelect = document.getElementById("longLoopOption");
  llSelect.innerHTML = "";
  (session.candidate_options || []).forEach((opt) => {
    const o = document.createElement("option");
    o.value = opt;
    o.textContent = opt;
    if (opt === adr.chosen_option) o.selected = true;
    llSelect.appendChild(o);
  });

  document.getElementById("shortLoopBtn").disabled = false;
  document.getElementById("longLoopBtn").disabled = false;

  // Also update Raw A2A Inspector in Tab 2
  const rawTrace = document.getElementById("rawTraceContainer");
  rawTrace.textContent = JSON.stringify(session.messages, null, 2);
}

// Start Council Debate
document.getElementById("startDebateBtn").addEventListener("click", async () => {
  const btn = document.getElementById("startDebateBtn");
  btn.disabled = true;
  btn.textContent = "⏳ Dibattito in corso...";

  const stream = document.getElementById("debateStream");
  stream.innerHTML = "";
  state.seenMessageIds.clear();
  document.getElementById("adrContainer").style.display = "none";
  document.getElementById("baselineCompareContainer").style.display = "none";
  document.getElementById("learningFeedbackToast").style.display = "none";

  const scenId = document.getElementById("scenarioSelect").value || null;
  const title = document.getElementById("scenTitle").value.trim();
  const prompt = document.getElementById("scenPrompt").value.trim();
  const options = document
    .getElementById("scenOptions")
    .value.split("\n")
    .map((s) => s.trim())
    .filter(Boolean);
  const qas = document
    .getElementById("scenQAs")
    .value.split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  const constraints = document
    .getElementById("scenConstraints")
    .value.split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  const useMemory = document.getElementById("useMemoryCheck").checked;
  const fastSim = document.getElementById("fastSimCheck").checked;

  try {
    const resp = await fetch(`/api/debate/start?fast_sim=${fastSim}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario_id: scenId,
        title: title,
        requirements_prompt: prompt,
        candidate_options: options,
        quality_attributes: qas,
        constraints: constraints,
        max_critique_rounds: 1,
        use_long_loop_memory: useMemory,
      }),
    });
    const session = await resp.json();
    state.currentSession = session;
    (session.messages || []).forEach((m) => appendLiveMessage(m));
    renderADR(session);
    document.getElementById("debateStatusBadge").textContent = `Completato in ${session.total_latency_ms}ms`;
  } catch (err) {
    console.error(err);
    alert("Errore durante il dibattito: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "▶ 1. Avvia Dibattito del Consiglio";
  }
});

// Short-Loop Human Feedback
document.getElementById("shortLoopBtn").addEventListener("click", async () => {
  if (!state.currentSession) return;
  const critique = document.getElementById("shortLoopInput").value.trim();
  if (!critique) {
    alert("Scrivi prima una tua osservazione o critica nella casella dell'Opzione 3A!");
    return;
  }
  const btn = document.getElementById("shortLoopBtn");
  btn.disabled = true;
  btn.textContent = "⏳ Gli agenti stanno ridiscutendo...";
  const fastSim = document.getElementById("fastSimCheck").checked;

  try {
    const resp = await fetch(`/api/debate/short-loop?fast_sim=${fastSim}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: state.currentSession.session_id,
        human_critique: critique,
        emphasized_quality_attributes: ["operability", "maintainability"],
      }),
    });
    const updatedSession = await resp.json();
    state.currentSession = updatedSession;
    (updatedSession.messages || []).forEach((m) => appendLiveMessage(m));
    renderADR(updatedSession);
  } catch (err) {
    alert("Errore Short-loop: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "💬 Invia Critica e Fai Ridiscutere gli Agenti";
  }
});

// Long-Loop Final Human Decision
document.getElementById("longLoopBtn").addEventListener("click", async () => {
  if (!state.currentSession) return;
  const finalOpt = document.getElementById("longLoopOption").value;
  const rationale = document.getElementById("longLoopRationale").value.trim();
  const btn = document.getElementById("longLoopBtn");
  btn.disabled = true;

  try {
    const resp = await fetch("/api/debate/long-loop", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: state.currentSession.session_id,
        final_chosen_option: finalOpt,
        human_rationale: rationale,
      }),
    });
    const res = await resp.json();
    const toast = document.getElementById("learningFeedbackToast");
    toast.style.display = "block";
    toast.innerHTML = `✅ <strong>Decisione salvata!</strong> Il Consiglio ha imparato la regola <code>${res.learning_update.new_principle.id}</code> e ha aggiornato la fiducia degli agenti!`;
    await loadAllInitialData();
  } catch (err) {
    alert("Errore Long-loop: " + err.message);
  } finally {
    btn.disabled = false;
  }
});

// Compare with Single-LLM Baselines on current scenario
document.getElementById("runBaselineBtn").addEventListener("click", async () => {
  const prompt = document.getElementById("scenPrompt").value.trim();
  const options = document
    .getElementById("scenOptions")
    .value.split("\n")
    .map((s) => s.trim())
    .filter(Boolean);
  const fastSim = document.getElementById("fastSimCheck").checked;
  const box = document.getElementById("baselineCompareContainer");
  box.style.display = "block";
  box.innerHTML = `<div class="card">⏳ Interrogazione dei singoli modelli AI da soli (senza dibattito)...</div>`;

  const resp = await fetch(`/api/baseline/compare?fast_sim=${fastSim}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      requirements_prompt: prompt,
      candidate_options: options,
    }),
  });
  const data = await resp.json();
  const rows = (data.single_llm_baselines || [])
    .map(
      (b) => `
      <tr>
        <td><strong>${b.llm_family}</strong><br/><span style="font-size:0.76rem;color:var(--muted);">${b.model}</span></td>
        <td><strong>${b.selected_option}</strong></td>
        <td>${Math.round(b.confidence * 100)}%</td>
        <td>${b.citation_count} fonti</td>
        <td style="font-size:0.82rem;color:var(--muted);">${b.summary_argument}</td>
      </tr>`
    )
    .join("");

  box.innerHTML = `
    <div class="card" style="margin-top:18px;">
      <div class="eyebrow">Slide 11 &mdash; Confronto con Baseline</div>
      <div class="card-title" style="margin-bottom:8px;">🤖 Cosa rispondono le AI Singole da sole (Senza Consiglio e Senza Dibattito)</div>
      <table class="data-table">
        <thead>
          <tr><th>Modello Singolo</th><th>Scelta</th><th>Sicurezza</th><th>Prove Citate</th><th>Motivazione (senza contraddittorio)</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
});

// Render Agent Pool (Tab 2)
function renderAgentPool(agents) {
  const grid = document.getElementById("agentPoolGrid");
  grid.innerHTML = agents
    .map(
      (a) => `
      <div class="card" style="margin-bottom:0;border-top:4px solid var(--primary);">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:1.6rem;">${a.icon || "🤖"}</span>
          <span class="pill ok">Fiducia: ${a.trust_weight}x</span>
        </div>
        <h3 style="margin-top:8px;font-size:1.05rem;">${a.name}</h3>
        <p style="font-size:0.82rem;color:var(--primary);font-weight:700;">Carattere: ${a.stance} &bull; ${a.llm_family}</p>
        <p style="font-size:0.78rem;color:var(--muted);margin:6px 0;">Provider: <code>${a.provider}</code> | Modello: <code>${a.model}</code></p>
        <p style="font-size:0.84rem;color:var(--ink);margin-bottom:12px;">${a.mandate}</p>
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span class="badge">Priorità: ${(a.priorities || []).join(", ")}</span>
          <button class="btn btn-outline" style="padding:4px 10px;font-size:0.76rem;" onclick="toggleAgentSeat('${a.agent_id}', ${!a.enabled})">
            ${a.enabled ? "Disattiva" : "Attiva"}
          </button>
        </div>
      </div>`
    )
    .join("");
}

window.toggleAgentSeat = async function (agentId, enabled) {
  await fetch(`/api/agents/${agentId}/toggle?enabled=${enabled}`, { method: "PATCH" });
  await loadAllInitialData();
};

document.getElementById("saveAgentBtn").addEventListener("click", async () => {
  const payload = {
    agent_id: document.getElementById("newAgentId").value.trim(),
    name: document.getElementById("newAgentName").value.trim(),
    stance: document.getElementById("newAgentStance").value.trim(),
    llm_family: document.getElementById("newAgentFamily").value.trim(),
    provider: document.getElementById("newAgentProvider").value,
    model: document.getElementById("newAgentModel").value.trim(),
    mandate: document.getElementById("newAgentMandate").value.trim(),
    priorities: document
      .getElementById("newAgentPriorities")
      .value.split(",")
      .map((s) => s.trim())
      .filter(Boolean),
    enabled: true,
  };
  await fetch("/api/agents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await loadAllInitialData();
  alert(`L'agente '${payload.name}' è stato aggiunto a caldo nel Consiglio!`);
});

document.getElementById("resetAgentsBtn").addEventListener("click", async () => {
  await fetch("/api/agents/reset", { method: "POST" });
  await loadAllInitialData();
});

// Render Knowledge Base & Long-Loop Memory (Tab 3)
function renderKnowledgeAndMemory(kbItems, memoryState) {
  const kbGrid = document.getElementById("kbGrid");
  kbGrid.innerHTML = kbItems
    .map(
      (item) => `
      <div class="card" style="margin-bottom:0;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
          <span class="badge cite">📚 ${item.id}</span>
          <span class="badge">${item.category}</span>
        </div>
        <h3 style="font-size:0.96rem;margin-bottom:6px;color:var(--ink);">${item.title}</h3>
        <p style="font-size:0.82rem;color:var(--muted);margin-bottom:8px;">${item.summary}</p>
        <div style="font-size:0.76rem;color:#15803d;margin-bottom:4px;"><strong>✔ Select when:</strong> ${(item.selection_conditions || []).join(", ")}</div>
        <div style="font-size:0.76rem;color:#dc2626;margin-bottom:6px;"><strong>✖ Reject when:</strong> ${(item.rejection_conditions || []).join(", ")}</div>
        <div style="font-size:0.75rem;color:var(--subtle);">Fonte: ${item.source}</div>
      </div>`
    )
    .join("");

  const memDiv = document.getElementById("memoryExplorerContainer");
  const weights = memoryState.agent_trust_weights || {};
  const principles = memoryState.learned_principles || [];

  const weightBars = Object.entries(weights)
    .map(
      ([aid, w]) => `
      <div style="margin-bottom:10px;">
        <div style="display:flex;justify-content:space-between;font-size:0.84rem;margin-bottom:3px;">
          <span><code>${aid}</code></span>
          <strong>Peso di fiducia: ${w}x</strong>
        </div>
        <div class="bar-track"><div class="bar-fill" style="width:${Math.min(100, (w / 2.0) * 100)}%;"></div></div>
      </div>`
    )
    .join("");

  const principlesHtml =
    principles.length > 0
      ? principles
          .map(
            (p) => `
          <div style="background:var(--surface-alt);padding:10px 12px;border-radius:8px;border:1px solid var(--line);margin-bottom:8px;">
            <span class="badge cite">${p.id}</span> <strong>Scelta Preferita: ${p.preferred_pattern}</strong>
            <p style="font-size:0.82rem;color:var(--muted);margin-top:4px;">${p.principle}</p>
          </div>`
          )
          .join("")
      : `<p style="font-size:0.84rem;color:var(--muted);">Nessuna regola imparata finora. Approva una decisione nella Scheda 1 (Opzione 3B) oppure avvia l'Esperimento B nella Scheda 4.</p>`;

  memDiv.innerHTML = `
    <h4 style="font-size:0.9rem;margin-bottom:8px;color:var(--ink);">Fiducia Guadagnata dagli Agenti:</h4>
    ${weightBars}
    <h4 style="font-size:0.9rem;margin:18px 0 8px;color:var(--ink);">Regole Aziendali Imparate (${principles.length}):</h4>
    ${principlesHtml}
  `;

  document.getElementById("memoryCountPill").textContent = `Regole Imparate: ${principles.length}`;
}

document.getElementById("resetMemoryBtn").addEventListener("click", async () => {
  await fetch("/api/memory/reset", { method: "POST" });
  await loadAllInitialData();
});

// Tab 4: Run Experiment A & Experiment B
document.getElementById("runExpABtn").addEventListener("click", async () => {
  const btn = document.getElementById("runExpABtn");
  const out = document.getElementById("expAResults");
  btn.disabled = true;
  out.innerHTML = "<p style='padding:12px;'>⏳ Calcolo in corso sui 12 Scenari di Test...</p>";
  try {
    const resp = await fetch("/api/evaluate/experiment-a?fast_sim=true", { method: "POST" });
    const data = await resp.json();
    const rows = (data.systems || [])
      .map(
        (s) => `
        <tr style="${s.system_type === "architect_council" ? "background:var(--green-soft);font-weight:700;" : ""}">
          <td>${s.system_name}</td>
          <td>
            <div style="display:flex;align-items:center;gap:8px;">
              <span>${s.accuracy_pct}%</span>
              <div class="bar-track" style="width:80px;"><div class="bar-fill" style="width:${s.accuracy_pct}%;"></div></div>
            </div>
          </td>
          <td>${s.weighted_quality_pct}%</td>
          <td>${s.avg_driver_coverage_pct || 100}%</td>
          <td>${s.avg_tradeoffs}</td>
        </tr>`
      )
      .join("");

    out.innerHTML = `
      <div style="display:flex;gap:12px;margin-bottom:14px;flex-wrap:wrap;">
        <div style="background:var(--surface-alt);padding:12px 16px;border-radius:10px;border:1px solid var(--line);flex:1;">
          <div style="font-size:0.78rem;color:var(--muted);">Miglior AI Singola da Sola</div>
          <div class="stat-big" style="color:var(--amber);">${data.best_single_llm_accuracy_pct}%</div>
        </div>
        <div style="background:var(--green-soft);padding:12px 16px;border-radius:10px;border:1px solid var(--green-border);flex:1;">
          <div style="font-size:0.78rem;color:#15803d;">Nostro Consiglio Completo</div>
          <div class="stat-big" style="color:var(--green);">${data.council_full_accuracy_pct}%</div>
        </div>
        <div style="background:var(--primary-soft);padding:12px 16px;border-radius:10px;border:1px solid #bfdbfe;flex:1;">
          <div style="font-size:0.78rem;color:var(--primary);">Vantaggio del Consiglio</div>
          <div class="stat-big">+${data.gain_over_best_single_pct}%</div>
        </div>
      </div>
      <table class="data-table">
        <thead>
          <tr><th>Sistema Valutato</th><th>Precisione Esatta</th><th>Qualità</th><th>Driver Coperti</th><th>Trade-off</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;
    await loadAllInitialData();
  } finally {
    btn.disabled = false;
  }
});

document.getElementById("runExpBBtn").addEventListener("click", async () => {
  const btn = document.getElementById("runExpBBtn");
  const out = document.getElementById("expBResults");
  btn.disabled = true;
  out.innerHTML = "<p style='padding:12px;'>⏳ Calcolo curva di apprendimento sui 12 Scenari di Test...</p>";
  try {
    const resp = await fetch("/api/evaluate/experiment-b?fast_sim=true", { method: "POST" });
    const data = await resp.json();
    const curveRows = (data.learning_curve || [])
      .map(
        (c) => `
        <tr>
          <td><strong>Tappa ${c.iteration}</strong> (dopo ${c.feedback_scenarios_seen} feedback)</td>
          <td>${c.learned_principles_count} regole</td>
          <td>
            <div style="display:flex;align-items:center;gap:8px;">
              <strong>${c.accuracy_pct}%</strong>
              <div class="bar-track" style="width:90px;"><div class="bar-fill" style="width:${c.accuracy_pct}%;"></div></div>
            </div>
          </td>
          <td>${c.weighted_quality_pct}%</td>
          <td>${c.avg_consensus_pct}%</td>
        </tr>`
      )
      .join("");

    out.innerHTML = `
      <div style="display:flex;gap:12px;margin-bottom:14px;flex-wrap:wrap;">
        <div style="background:var(--surface-alt);padding:12px 16px;border-radius:10px;border:1px solid var(--line);flex:1;">
          <div style="font-size:0.78rem;color:var(--muted);">Prima del Feedback (Tappa 0)</div>
          <div class="stat-big" style="color:var(--amber);">${data.accuracy_before_feedback_pct}%</div>
        </div>
        <div style="background:var(--green-soft);padding:12px 16px;border-radius:10px;border:1px solid var(--green-border);flex:1;">
          <div style="font-size:0.78rem;color:#15803d;">Dopo il Feedback (Tappa 3)</div>
          <div class="stat-big" style="color:var(--green);">${data.accuracy_after_feedback_pct}%</div>
        </div>
        <div style="background:var(--primary-soft);padding:12px 16px;border-radius:10px;border:1px solid #bfdbfe;flex:1;">
          <div style="font-size:0.78rem;color:var(--primary);">Miglioramento Imparato</div>
          <div class="stat-big">+${data.accuracy_improvement_pct}%</div>
        </div>
      </div>
      <table class="data-table">
        <thead>
          <tr><th>Tappa di Apprendimento</th><th>Memoria</th><th>Precisione su Test</th><th>Qualità</th><th>Consenso</th></tr>
        </thead>
        <tbody>${curveRows}</tbody>
      </table>
    `;
    await loadAllInitialData();
  } finally {
    btn.disabled = false;
  }
});

// Load Scenarios, Agents, Knowledge Base, Memory, and Docs
async function loadAllInitialData() {
  try {
    const [metaRes, scenRes, kbRes, memRes, docsRes] = await Promise.all([
      fetch("/api/meta").then((r) => r.json()),
      fetch("/api/scenarios").then((r) => r.json()),
      fetch("/api/knowledge").then((r) => r.json()),
      fetch("/api/memory").then((r) => r.json()),
      fetch("/api/docs/list").then((r) => r.json()),
    ]);

    state.scenarios = scenRes.all || [];
    state.agents = metaRes.agents || [];
    state.kbItems = kbRes.items || [];
    state.docs = docsRes.docs || [];

    // Team list
    const teamList = document.getElementById("teamList");
    if (teamList && metaRes.team_members) {
      teamList.innerHTML = metaRes.team_members.map((m) => `<li>&#128100; ${m}</li>`).join("");
    }

    // Populate Scenario dropdown
    const sel = document.getElementById("scenarioSelect");
    if (sel && sel.options.length === 0) {
      state.scenarios.forEach((s) => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = `[${s.id} • ${s.split === "feedback" ? "ALLENAMENTO" : "TEST ESAME"}] ${s.title}`;
        sel.appendChild(opt);
      });
      sel.addEventListener("change", () => {
        const found = state.scenarios.find((x) => x.id === sel.value);
        if (found) {
          document.getElementById("scenTitle").value = found.title;
          document.getElementById("scenPrompt").value = found.prompt;
          document.getElementById("scenOptions").value = (found.options || []).join("\n");
          document.getElementById("scenQAs").value = (found.quality_attributes || []).join(", ");
          document.getElementById("scenConstraints").value = (found.constraints || []).join(", ");
        }
      });
    }

    renderAgentPool(state.agents);
    renderKnowledgeAndMemory(state.kbItems, memRes);

    // Docs list
    const docList = document.getElementById("docListContainer");
    if (docList && state.docs.length > 0) {
      docList.innerHTML = state.docs
        .map(
          (d, idx) =>
            `<button class="btn btn-outline" style="justify-content:flex-start;text-align:left;" onclick="showDoc(${idx})">📄 ${d.title}</button>`
        )
        .join("");
      if (document.getElementById("docViewerContent").textContent.startsWith("Seleziona")) {
        window.showDoc(0);
      }
    }
  } catch (e) {
    console.error("Failed loading initial data:", e);
  }
}

window.showDoc = function (idx) {
  const doc = state.docs[idx];
  if (!doc) return;
  document.getElementById("activeDocTitle").textContent = "📖 " + doc.title;
  document.getElementById("docViewerContent").textContent = doc.content;
};

window.addEventListener("DOMContentLoaded", () => {
  connectSSE();
  loadAllInitialData();
});
