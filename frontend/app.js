// ============================================================================
// AI Assisted Software Architecting Council — Frontend Controller
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
    pill.textContent = "● A2A Bus Live (SSE)";
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
    pill.textContent = "○ Reconnecting Bus...";
  };
}

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
      .map((cid) => `<span class="badge cite" title="Grounded KB / Memory Provenance">[${cid}]</span>`)
      .join(" ");
  }

  let mindChangedBadge = "";
  if (contract && contract.mind_changed) {
    mindChangedBadge = `<span class="badge changed">🔄 Mind Changed: ${contract.change_reason || "Peer Evidence"}</span>`;
  }

  let tradeoffsHtml = "";
  if (contract && contract.tradeoffs && Object.keys(contract.tradeoffs).length > 0) {
    const items = Object.entries(contract.tradeoffs)
      .map(([k, v]) => `<li><strong>${k}:</strong> ${v}</li>`)
      .join("");
    tradeoffsHtml = `<ul style="margin-top:6px;padding-left:18px;font-size:0.82rem;color:var(--muted);">${items}</ul>`;
  }

  const confBadge = contract
    ? `<span class="badge">Confidence: ${Math.round(contract.confidence * 100)}%</span>`
    : "";

  card.innerHTML = `
    <div class="msg-header">
      <div class="msg-sender">
        <span>${msg.sender_name}</span>
        <span class="badge" style="color:#fff;">${msg.sender_stance}</span>
        <span class="badge">${msg.llm_family} (${msg.llm_model})</span>
        ${confBadge}
        ${mindChangedBadge}
      </div>
      <span class="badge">${msg.phase}${msg.round_num ? " R" + msg.round_num : ""} &bull; ${msg.latency_ms}ms</span>
    </div>
    <div class="msg-body">${formatMarkdownInline(msg.content)}</div>
    ${tradeoffsHtml}
    <div class="msg-meta">
      <span>ID: <code>${msg.message_id}</code> &rarr; <code>${msg.recipient_id}</code></span>
      <span>Mode: <code>${msg.execution_mode}</code></span>
      ${citationsHtml}
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
    .map(([agent, opt]) => `<li><strong>${agent}:</strong> ${opt}</li>`)
    .join("");

  const dissentHtml =
    adr.minority_dissent && adr.minority_dissent.length > 0
      ? adr.minority_dissent
          .map(
            (d) => `
          <div class="dissent-card">
            <strong>⚠️ Minority Dissent — ${d.agent_name} (${d.stance} &bull; ${d.llm_family})</strong><br/>
            Preferred: <strong>${d.preferred_option}</strong><br/>
            Rationale: ${d.rationale}
            <div style="margin-top:4px;">Citations: ${(d.citations || []).map((c) => `[${c}]`).join(", ")}</div>
          </div>`
          )
          .join("")
      : `<div style="margin-top:8px;font-size:0.85rem;color:#86efac;">✓ Unanimous Council Consensus (0 Minority Dissents)</div>`;

  const tradeoffsHtml = Object.entries(adr.tradeoffs || {})
    .map(([k, v]) => `<li><strong>${k}:</strong> ${v}</li>`)
    .join("");

  container.innerHTML = `
    <div class="adr-box">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:10px;">
        <div>
          <div class="eyebrow" style="color:#86efac;">Phase 5 &mdash; Synthesized Architecture Decision Record</div>
          <h3 style="font-size:1.2rem;font-weight:900;">${adr.adr_id}: ${adr.title}</h3>
        </div>
        <div style="display:flex;gap:8px;align-items:center;">
          <span class="pill ok">${adr.consensus_type} (${Math.round(adr.consensus_score * 100)}%)</span>
          <span class="pill accent">${adr.status}</span>
        </div>
      </div>

      <p style="font-size:0.95rem;margin-bottom:10px;">
        <strong>Selected Decision:</strong> <span style="color:#86efac;font-weight:800;font-size:1.05rem;">${adr.chosen_option}</span>
      </p>
      <p style="font-size:0.88rem;color:var(--ink);margin-bottom:10px;">${formatMarkdownInline(adr.rationale)}</p>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:12px;">
        <div style="background:rgba(0,0,0,0.22);padding:12px;border-radius:10px;">
          <strong style="font-size:0.84rem;color:var(--muted);">Council Vote Breakdown:</strong>
          <ul style="padding-left:18px;margin-top:6px;font-size:0.84rem;">${votesHtml}</ul>
        </div>
        <div style="background:rgba(0,0,0,0.22);padding:12px;border-radius:10px;">
          <strong style="font-size:0.84rem;color:var(--muted);">Synthesized Trade-offs &amp; Citations:</strong>
          <ul style="padding-left:18px;margin-top:6px;font-size:0.82rem;">${tradeoffsHtml}</ul>
          <div style="margin-top:6px;font-size:0.8rem;color:#f0abfc;">
            Provenance Citations: ${(adr.citations || []).map((c) => `[${c}]`).join(", ")}
          </div>
        </div>
      </div>

      <div style="margin-top:12px;">
        <strong style="font-size:0.85rem;color:var(--muted);">Minority View &amp; Dissent Log (Slide 7):</strong>
        ${dissentHtml}
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
  btn.textContent = "⏳ Council Debating...";

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
    document.getElementById("debateStatusBadge").textContent = `Completed (${session.total_latency_ms}ms)`;
  } catch (err) {
    console.error(err);
    alert("Error running debate: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "⚡ Start Council Debate";
  }
});

// Short-Loop Human Feedback
document.getElementById("shortLoopBtn").addEventListener("click", async () => {
  if (!state.currentSession) return;
  const critique = document.getElementById("shortLoopInput").value.trim();
  if (!critique) {
    alert("Please enter your Human Architect critique or constraint for the Short Loop.");
    return;
  }
  const btn = document.getElementById("shortLoopBtn");
  btn.disabled = true;
  btn.textContent = "⏳ Revising Proposal...";
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
    alert("Short-loop error: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "💬 Send Short-Loop Critique & Revise Proposal";
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
    toast.innerHTML = `✓ <strong>Long-Loop Updated!</strong> Stored Principle <code>${res.learning_update.new_principle.id}</code> and updated Per-Agent Trust Weights.`;
    await loadAllInitialData();
  } catch (err) {
    alert("Long-loop error: " + err.message);
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
  box.innerHTML = `<div class="card">⏳ Running Single-LLM Baselines (no roles, no debate, no KB memory)...</div>`;

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
        <td>${b.selected_option}</td>
        <td>${Math.round(b.confidence * 100)}%</td>
        <td>${b.citation_count} citations</td>
        <td style="font-size:0.8rem;color:var(--muted);">${b.summary_argument}</td>
      </tr>`
    )
    .join("");

  box.innerHTML = `
    <div class="card">
      <div class="eyebrow">Slide 11 &mdash; Single-Prompt Baseline Comparison</div>
      <div class="card-title" style="margin-bottom:8px;">🤖 Single LLMs Alone (No Agents, No Debate, No Feedback Loop)</div>
      <table class="data-table">
        <thead>
          <tr><th>Single LLM</th><th>Selected Option</th><th>Conf.</th><th>Evidence</th><th>Unchallenged Output</th></tr>
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
      <div class="card" style="margin-bottom:0;border-top:4px solid ${a.color || "#b800e6"};">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:1.5rem;">${a.icon || "🤖"}</span>
          <span class="badge" style="color:#86efac;">Trust Weight: ${a.trust_weight}x</span>
        </div>
        <h3 style="margin-top:8px;font-size:1.05rem;">${a.name}</h3>
        <p style="font-size:0.8rem;color:#f0abfc;font-weight:700;">Stance: ${a.stance} &bull; ${a.llm_family}</p>
        <p style="font-size:0.78rem;color:var(--muted);margin:6px 0;">Provider: <code>${a.provider}</code> | Model: <code>${a.model}</code></p>
        <p style="font-size:0.82rem;color:var(--ink);margin-bottom:10px;">${a.mandate}</p>
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span class="badge">Priorities: ${(a.priorities || []).join(", ")}</span>
          <button class="btn btn-outline" style="padding:3px 9px;font-size:0.75rem;" onclick="toggleAgentSeat('${a.agent_id}', ${!a.enabled})">
            ${a.enabled ? "Disable" : "Enable"}
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
  alert(`Agent '${payload.name}' hot-swapped into the active Council pool!`);
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
          <span class="badge cite">[${item.id}]</span>
          <span class="badge">${item.category}</span>
        </div>
        <h3 style="font-size:0.96rem;margin-bottom:6px;">${item.title}</h3>
        <p style="font-size:0.82rem;color:var(--muted);margin-bottom:8px;">${item.summary}</p>
        <div style="font-size:0.75rem;color:#86efac;">Provenance Source: ${item.source}</div>
      </div>`
    )
    .join("");

  const memDiv = document.getElementById("memoryExplorerContainer");
  const weights = memoryState.agent_trust_weights || {};
  const principles = memoryState.learned_principles || [];

  const weightBars = Object.entries(weights)
    .map(
      ([aid, w]) => `
      <div style="margin-bottom:8px;">
        <div style="display:flex;justify-content:space-between;font-size:0.82rem;">
          <span><code>${aid}</code></span>
          <strong>${w}x trust multiplier</strong>
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
          <div style="background:var(--bg);padding:10px 12px;border-radius:9px;border:1px solid var(--line);margin-bottom:8px;">
            <span class="badge cite">[${p.id}]</span> <strong>Preferred: ${p.preferred_pattern}</strong>
            <p style="font-size:0.82rem;color:var(--muted);margin-top:4px;">${p.principle}</p>
          </div>`
          )
          .join("")
      : `<p style="font-size:0.84rem;color:var(--muted);">No learned principles yet. Commit a final decision in Tab 1 or run Experiment B in Tab 4.</p>`;

  memDiv.innerHTML = `
    <h4 style="font-size:0.9rem;margin-bottom:8px;color:var(--muted);">Per-Model / Per-Agent Trust Weights:</h4>
    ${weightBars}
    <h4 style="font-size:0.9rem;margin:16px 0 8px;color:var(--muted);">Learned Architectural Principles (${principles.length}):</h4>
    ${principlesHtml}
  `;

  document.getElementById("memoryCountPill").textContent = `Learned Principles: ${principles.length}`;
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
  out.innerHTML = "<p>⏳ Evaluating Single-LLM Baselines vs. Architect Council on 12 Held-Out Test Scenarios...</p>";
  try {
    const resp = await fetch("/api/evaluate/experiment-a?fast_sim=true", { method: "POST" });
    const data = await resp.json();
    const rows = (data.systems || [])
      .map(
        (s) => `
        <tr style="${s.system_type === "architect_council" ? "background:rgba(34,197,94,0.09);font-weight:700;" : ""}">
          <td>${s.system_name}</td>
          <td>
            <div style="display:flex;align-items:center;gap:8px;">
              <span>${s.accuracy_pct}%</span>
              <div class="bar-track" style="width:90px;"><div class="bar-fill" style="width:${s.accuracy_pct}%;"></div></div>
            </div>
          </td>
          <td>${s.weighted_quality_pct}%</td>
          <td>${s.avg_tradeoffs}</td>
          <td>${s.avg_citations}</td>
        </tr>`
      )
      .join("");

    out.innerHTML = `
      <div style="display:flex;gap:14px;margin-bottom:12px;flex-wrap:wrap;">
        <div style="background:var(--bg);padding:12px 16px;border-radius:10px;border:1px solid var(--line);flex:1;">
          <div style="font-size:0.78rem;color:var(--muted);">Best Single LLM Alone</div>
          <div class="stat-big" style="color:var(--amber);">${data.best_single_llm_accuracy_pct}%</div>
        </div>
        <div style="background:var(--bg);padding:12px 16px;border-radius:10px;border:1px solid var(--line);flex:1;">
          <div style="font-size:0.78rem;color:var(--muted);">Full Architect Council</div>
          <div class="stat-big" style="color:var(--green);">${data.council_full_accuracy_pct}%</div>
        </div>
        <div style="background:var(--bg);padding:12px 16px;border-radius:10px;border:1px solid var(--line);flex:1;">
          <div style="font-size:0.78rem;color:var(--muted);">Council Gain vs. Best Single</div>
          <div class="stat-big">+${data.gain_over_best_single_pct}%</div>
        </div>
      </div>
      <table class="data-table">
        <thead>
          <tr><th>System</th><th>Exact Accuracy</th><th>Quality Score</th><th>Avg Trade-offs</th><th>Avg Citations</th></tr>
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
  out.innerHTML = "<p>⏳ Running 4-Iteration Feedback Learning Curve on 12 Held-Out Test Set Scenarios...</p>";
  try {
    const resp = await fetch("/api/evaluate/experiment-b?fast_sim=true", { method: "POST" });
    const data = await resp.json();
    const curveRows = (data.learning_curve || [])
      .map(
        (c) => `
        <tr>
          <td><strong>Iteration ${c.iteration}</strong> (${c.feedback_scenarios_seen} Feedback Scenarios)</td>
          <td>${c.learned_principles_count} principles</td>
          <td>
            <div style="display:flex;align-items:center;gap:8px;">
              <strong>${c.accuracy_pct}%</strong>
              <div class="bar-track" style="width:100px;"><div class="bar-fill" style="width:${c.accuracy_pct}%;"></div></div>
            </div>
          </td>
          <td>${c.weighted_quality_pct}%</td>
          <td>${c.avg_consensus_pct}%</td>
        </tr>`
      )
      .join("");

    out.innerHTML = `
      <div style="display:flex;gap:14px;margin-bottom:12px;flex-wrap:wrap;">
        <div style="background:var(--bg);padding:12px 16px;border-radius:10px;border:1px solid var(--line);flex:1;">
          <div style="font-size:0.78rem;color:var(--muted);">Before Feedback (Iter 0)</div>
          <div class="stat-big" style="color:var(--amber);">${data.accuracy_before_feedback_pct}%</div>
        </div>
        <div style="background:var(--bg);padding:12px 16px;border-radius:10px;border:1px solid var(--line);flex:1;">
          <div style="font-size:0.78rem;color:var(--muted);">After Feedback (Iter 3)</div>
          <div class="stat-big" style="color:var(--green);">${data.accuracy_after_feedback_pct}%</div>
        </div>
        <div style="background:var(--bg);padding:12px 16px;border-radius:10px;border:1px solid var(--line);flex:1;">
          <div style="font-size:0.78rem;color:var(--muted);">Held-Out Accuracy Gain</div>
          <div class="stat-big">+${data.accuracy_improvement_pct}%</div>
        </div>
      </div>
      <table class="data-table">
        <thead>
          <tr><th>Learning Checkpoint</th><th>Memory Size</th><th>Held-Out Test Accuracy</th><th>Quality Score</th><th>Avg Consensus</th></tr>
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
        opt.textContent = `[${s.id} • ${s.split.toUpperCase()}] ${s.title}`;
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
      if (document.getElementById("docViewerContent").textContent.startsWith("Select a document")) {
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
  document.getElementById("activeDocTitle").textContent = "📐 " + doc.title;
  document.getElementById("docViewerContent").textContent = doc.content;
};

window.addEventListener("DOMContentLoaded", () => {
  connectSSE();
  loadAllInitialData();
});

