const state = {
  activeSessionId: "",
  activeSession: null,
};

const $ = (id) => document.getElementById(id);

function announce(message) {
  $("announcer").textContent = message;
}

function status(message, tone = "default") {
  const el = $("connectionState");
  el.textContent = message;
  el.dataset.tone = tone;
  announce(message);
}

function currentToken() {
  return $("tokenInput").value.trim();
}

async function api(path, method = "GET", body = null) {
  const headers = {};
  const token = currentToken();
  if (token) {
    headers["X-Ephux-Token"] = token;
  }
  if (body !== null) {
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(path, {
    method,
    headers,
    body: body === null ? null : JSON.stringify(body),
  });
  const text = await response.text();
  let payload = text;
  try {
    payload = JSON.parse(text);
  } catch {}
  if (!response.ok) {
    throw new Error(typeof payload === "string" ? payload : JSON.stringify(payload, null, 2));
  }
  return payload;
}

function pretty(value) {
  return JSON.stringify(value ?? {}, null, 2);
}

function metric(label, value, tone = "") {
  return `<article class="metric"><span>${label}</span><strong class="${tone}">${value}</strong></article>`;
}

function renderTimeline(events) {
  const root = $("timeline");
  root.innerHTML = "";
  for (const event of events || []) {
    const article = document.createElement("article");
    article.innerHTML = `
      <strong>${event.type || "event"}</strong>
      <div class="mono">${event.event_id || ""}</div>
      <pre>${pretty(event)}</pre>
    `;
    root.appendChild(article);
  }
}

function renderSession(session) {
  state.activeSession = session;
  state.activeSessionId = session?.session_id || "";
  $("activeSession").textContent = state.activeSessionId || "No session selected";
  $("metrics").innerHTML = [
    metric("Epistemic", session?.current_epistemic_state || "UNRESOLVED"),
    metric("Action", session?.current_action_state || "HOLD"),
    metric("Events", String(session?.event_count || 0)),
    metric("Artifacts", String((session?.artifacts || []).length)),
  ].join("");
  $("candidateSpectrum").textContent = pretty(session?.candidate_spectrum || {});
  $("claimsEvidence").textContent = pretty({
    decision_critical_claims: session?.decision_critical_claims || [],
    supporting_evidence: session?.supporting_evidence || [],
    contradictory_evidence: session?.contradictory_evidence || [],
  });
  $("holdsRecovery").textContent = pretty({
    hold_reasons: session?.hold_reasons || [],
    retract_reasons: session?.retract_reasons || [],
    recovery_routes: session?.recovery_routes || [],
  });
  $("associationsScars").textContent = pretty({
    associations: session?.associations || [],
    contradiction_scars: session?.contradiction_scars || [],
    review_events: session?.review_events || [],
  });
  $("proposalState").textContent = pretty({
    latest_action_proposal: session?.latest_action_proposal,
    latest_commit_decision: session?.latest_commit_decision,
    report_location: session?.report_location,
  });
  $("labRuns").textContent = pretty(session?.lab_runs || []);
  renderTimeline(session?.timeline || []);
  status(`Loaded session ${state.activeSessionId}.`, "ok");
}

function sessionButton(session) {
  const button = document.createElement("button");
  button.className = session.session_id === state.activeSessionId ? "active" : "";
  button.innerHTML = `
    <strong>${session.purpose || "Untitled session"}</strong><br>
    <span class="mono">${session.session_id}</span><br>
    <span>${session.final_basin?.epistemic || "UNRESOLVED"} / ${session.final_basin?.action || "HOLD"}</span>
  `;
  button.addEventListener("click", async () => {
    try {
      renderSession(await api(`/sessions/${session.session_id}`));
      await loadSessions();
    } catch (error) {
      status(`Failed to reopen session: ${error.message}`, "danger");
    }
  });
  return button;
}

async function loadSessions() {
  try {
    const payload = await api("/sessions");
    const root = $("sessionList");
    root.innerHTML = "";
    for (const session of payload.sessions || []) {
      root.appendChild(sessionButton(session));
    }
    if (!payload.sessions?.length) {
      root.textContent = "No persisted sessions yet.";
    }
  } catch (error) {
    status(`Unable to load sessions: ${error.message}`, "danger");
  }
}

async function refreshSession() {
  if (!state.activeSessionId) {
    status("Select or create a session first.", "warn");
    return;
  }
  renderSession(await api(`/sessions/${state.activeSessionId}`));
}

async function createSession() {
  const payload = {
    purpose: $("purposeInput").value.trim(),
    context: $("contextInput").value.trim(),
  };
  renderSession(await api("/sessions", "POST", payload));
  await loadSessions();
}

async function startActivation() {
  const payload = {
    purpose: $("purposeInput").value.trim(),
    provider_preference: $("providerPreference").value,
  };
  const activation = await api("/activation", "POST", payload);
  renderSession(await api(`/sessions/${activation.session_id}`));
  await loadSessions();
}

async function submitIntake() {
  const payload = {
    session_id: state.activeSessionId || "",
    text: $("intakeText").value,
    sanitization_evidence: [$("sanitizationEvidence").value].filter(Boolean),
  };
  const result = await api("/guardian/intake", "POST", payload);
  renderSession(await api(`/sessions/${result.session_id}`));
  await loadSessions();
}

async function runAction() {
  const payload = {
    step_id: $("actionStepId").value.trim(),
    summary: $("actionSummary").value.trim(),
    code: $("actionCode").value,
  };
  const result = await api(`/sessions/${state.activeSessionId}/actions`, "POST", payload);
  $("proposalState").textContent = pretty(result);
  await refreshSession();
}

async function submitEvidence() {
  await api(`/sessions/${state.activeSessionId}/evidence`, "POST", {
    detail: $("evidenceText").value,
    temporary_artifact_text: $("evidenceText").value,
  });
  await refreshSession();
}

async function submitClaim() {
  const statement = $("claimText").value;
  const contradictory = statement.toLowerCase().includes("contradiction");
  await api(`/sessions/${state.activeSessionId}/claims`, "POST", {
    statement,
    supporting_evidence: contradictory ? [] : ["ui evidence"],
    contradictory_evidence: contradictory ? ["ui contradiction"] : [],
  });
  await refreshSession();
}

async function proposeCommit() {
  const payload = {
    summary: $("actionSummary").value || "UI commit proposal",
    completion_claim: $("claimText").value || "Deployment verified.",
  };
  const result = await api(`/sessions/${state.activeSessionId}/commit`, "POST", payload);
  $("proposalState").textContent = pretty(result);
  await refreshSession();
}

async function holdSession() {
  await api(`/sessions/${state.activeSessionId}/hold`, "POST", {
    reason: $("reviewNote").value || "UI hold",
    required_evidence: ["human-review"],
  });
  await refreshSession();
}

async function retractSession() {
  await api(`/sessions/${state.activeSessionId}/retract`, "POST", {
    reason: $("reviewNote").value || "UI retract",
    contradictory_evidence: ["human-review contradiction"],
  });
  await refreshSession();
}

async function submitReview() {
  const payload = {
    review_action: $("reviewAction").value,
    note: $("reviewNote").value,
    reviewer: "local-human-review",
    provenance: "ui-human-review",
  };
  await api(`/sessions/${state.activeSessionId}/review`, "POST", payload);
  await refreshSession();
}

async function exportSession() {
  if (!state.activeSessionId) {
    status("No active session to export.", "warn");
    return;
  }
  const bundle = await api(`/sessions/${state.activeSessionId}/export`);
  const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${state.activeSessionId}-bundle.json`;
  link.click();
  URL.revokeObjectURL(url);
}

async function runEvaluationLab() {
  const result = await api(`/sessions/${state.activeSessionId}/labs/evaluation`, "POST", {
    requested_by: "ephux-local-ui",
  });
  $("labRuns").textContent = pretty(result);
  await refreshSession();
}

async function runNaturalMathLab() {
  const result = await api(`/sessions/${state.activeSessionId}/labs/natural-math`, "POST", {
    requested_by: "ephux-local-ui",
  });
  $("labRuns").textContent = pretty(result);
  await refreshSession();
}

async function importBundle(event) {
  const file = event.target.files?.[0];
  if (!file) {
    return;
  }
  const payload = JSON.parse(await file.text());
  const session = await api("/sessions/import", "POST", payload);
  renderSession(session);
  await loadSessions();
}

function openReport() {
  if (!state.activeSessionId) {
    status("No active session report to open.", "warn");
    return;
  }
  window.open(`/sessions/${state.activeSessionId}/report?format=html`, "_blank", "noopener");
}

function bind(id, fn) {
  $(id).addEventListener("click", async () => {
    try {
      if (!currentToken()) {
        status("Enter the local token before calling the service.", "warn");
        return;
      }
      await fn();
    } catch (error) {
      status(error.message, "danger");
    }
  });
}

window.addEventListener("online", () => status("Loopback connection restored.", "ok"));
window.addEventListener("offline", () => status("Offline shell active. No completion is fabricated offline.", "warn"));

bind("refreshSessions", loadSessions);
bind("createSession", createSession);
bind("startActivation", startActivation);
bind("submitIntake", submitIntake);
bind("runAction", runAction);
bind("submitEvidence", submitEvidence);
bind("submitClaim", submitClaim);
bind("proposeCommit", proposeCommit);
bind("holdSession", holdSession);
bind("retractSession", retractSession);
bind("submitReview", submitReview);
bind("refreshSession", refreshSession);
bind("exportSession", exportSession);
bind("openReport", async () => openReport());
bind("runEvaluationLab", runEvaluationLab);
bind("runNaturalMathLab", runNaturalMathLab);
$("importBundle").addEventListener("change", async (event) => {
  try {
    if (!currentToken()) {
      status("Enter the local token before importing a bundle.", "warn");
      return;
    }
    await importBundle(event);
  } catch (error) {
    status(error.message, "danger");
  }
});

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {
    status("Installable shell unavailable, continuing without service worker.", "warn");
  });
}

status("Enter the local token to work with persisted sessions.", "warn");
