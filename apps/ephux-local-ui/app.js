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

function selectedParticipant() {
  return $("participantSelect")?.value ?? "";
}

function selectedVisibility() {
  return $("visibilitySelect")?.value ?? "shared-project";
}

function selectedVisibilityEnum() {
  return selectedVisibility().replace(/-/g, "_").toUpperCase();
}

function explicitParticipantPayload(extra = {}) {
  return {
    participant: selectedParticipant(),
    participant_mode: "explicit",
    participant_source: "explicit",
    ...extra,
  };
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

function renderGovernanceViews(memoryState, narrativeState, privacyState) {
  $("memoryState").textContent = pretty({
    viewer_participant: memoryState?.viewer_participant,
    purpose: memoryState?.purpose,
    items: memoryState?.items || [],
    retrievals: memoryState?.retrievals || [],
    replay_receipts: memoryState?.replay_receipts || [],
  });
  $("narrativeState").textContent = pretty({
    participant_histories: narrativeState?.participant_histories || {},
    records: narrativeState?.records || [],
  });
  $("privacyState").textContent = pretty(privacyState || {});
}

function renderConnectorViews(connectors, actions) {
  $("connectorInventory").textContent = pretty(connectors || []);
  $("externalActionState").textContent = pretty(actions || {});
}

function renderConsciousnessViews(consciousness) {
  $("consciousnessState").textContent = pretty(consciousness || {});
  $("consciousnessWorkspace").textContent = pretty(consciousness?.workspace || {});
  $("consciousnessEpisodes").textContent = pretty(consciousness?.episodes || []);
}

async function refreshGovernanceViews() {
  if (!state.activeSessionId) {
    return;
  }
  const participant = encodeURIComponent(selectedParticipant());
  const [memoryState, narrativeState] = await Promise.all([
    api(`/sessions/${state.activeSessionId}/memory?participant=${participant}`),
    api(`/sessions/${state.activeSessionId}/narrative?participant=${participant}`),
  ]);
  renderGovernanceViews(memoryState, narrativeState, memoryState?.privacy || {});
}

async function refreshConnectorViews() {
  const connectors = await api("/connectors");
  let actions = {};
  if (state.activeSessionId) {
    const participant = encodeURIComponent(selectedParticipant());
    actions = await api(`/sessions/${state.activeSessionId}/external-actions?participant=${participant}`);
  }
  renderConnectorViews(connectors?.connectors || [], actions);
}

async function refreshConsciousnessViews() {
  if (!state.activeSessionId) {
    return;
  }
  renderConsciousnessViews(await api(`/sessions/${state.activeSessionId}/consciousness`));
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
  renderGovernanceViews(
    {
      viewer_participant: selectedParticipant() || "UNKNOWN",
      purpose: session?.purpose || "",
      items: session?.memory_items || [],
      retrievals: session?.memory_retrievals || [],
      replay_receipts: session?.memory_replay_receipts || [],
    },
    {
      records: session?.team_narrative || [],
      participant_histories: Object.fromEntries((session?.team_narrative || []).map((item) => [item.participant_id, item])),
    },
    session?.privacy_governance || {}
  );
  renderConnectorViews(session?.connectors || [], {
    session_id: state.activeSessionId,
    external_actions: session?.external_actions || [],
  });
  renderConsciousnessViews(session?.consciousness || {});
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
    visibility_scope: selectedVisibilityEnum(),
    ...explicitParticipantPayload(),
  });
  await refreshSession();
  await refreshGovernanceViews();
}

async function submitClaim() {
  const statement = $("claimText").value;
  const contradictory = statement.toLowerCase().includes("contradiction");
  await api(`/sessions/${state.activeSessionId}/claims`, "POST", {
    statement,
    supporting_evidence: contradictory ? [] : ["ui evidence"],
    contradictory_evidence: contradictory ? ["ui contradiction"] : [],
    visibility_scope: selectedVisibilityEnum(),
    ...explicitParticipantPayload(),
  });
  await refreshSession();
  await refreshGovernanceViews();
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

async function retrieveMemory() {
  const result = await api(`/sessions/${state.activeSessionId}/memory/retrieve`, "POST", explicitParticipantPayload({
    purpose: $("retrievalPurpose").value.trim(),
  }));
  $("memoryState").textContent = pretty(result);
  await refreshGovernanceViews();
}

async function promoteMemory() {
  const result = await api(`/sessions/${state.activeSessionId}/memory/promote`, "POST", explicitParticipantPayload({
    memory_id: $("memoryId").value.trim(),
    note: $("memoryNote").value.trim() || "verified-use",
    visibility_scope: selectedVisibility(),
    provenance: "ephux-local-ui",
  }));
  $("memoryState").textContent = pretty(result);
  await refreshSession();
  await refreshGovernanceViews();
}

async function demoteMemory() {
  const contradiction = $("memoryContradiction").value.trim();
  const result = await api(`/sessions/${state.activeSessionId}/memory/demote`, "POST", explicitParticipantPayload({
    memory_id: $("memoryId").value.trim(),
    note: $("memoryNote").value.trim() || "failed-use",
    contradiction_detail: contradiction,
    recovery_route_id: $("recoveryRouteId").value.trim(),
    recovery_status: contradiction ? "open" : "",
    provenance: "ephux-local-ui",
  }));
  $("memoryState").textContent = pretty(result);
  await refreshSession();
  await refreshGovernanceViews();
}

async function pruneMemory() {
  const result = await api(`/sessions/${state.activeSessionId}/memory/prune`, "POST", explicitParticipantPayload({
    memory_id: $("memoryId").value.trim(),
    reason: $("privacyReason").value.trim() || "retention-expiry",
    provenance: "ephux-local-ui",
  }));
  $("memoryState").textContent = pretty(result);
  await refreshSession();
  await refreshGovernanceViews();
}

async function addContribution() {
  const result = await api(`/sessions/${state.activeSessionId}/narrative/contributions`, "POST", explicitParticipantPayload({
    contribution: $("contributionText").value.trim(),
    visibility_scope: selectedVisibility(),
  }));
  $("narrativeState").textContent = pretty(result);
  await refreshSession();
  await refreshGovernanceViews();
}

async function addDecision() {
  const result = await api(`/sessions/${state.activeSessionId}/narrative/decisions`, "POST", explicitParticipantPayload({
    decision: $("decisionText").value.trim(),
    superseded_decision: $("supersededDecisionText").value.trim(),
    visibility_scope: selectedVisibility(),
  }));
  $("narrativeState").textContent = pretty(result);
  await refreshSession();
  await refreshGovernanceViews();
}

async function addDisagreement() {
  const result = await api(`/sessions/${state.activeSessionId}/narrative/disagreements`, "POST", explicitParticipantPayload({
    disagreement: $("disagreementText").value.trim(),
    unresolved_question: $("unresolvedQuestionText").value.trim(),
    visibility_scope: selectedVisibility(),
  }));
  $("narrativeState").textContent = pretty(result);
  await refreshSession();
  await refreshGovernanceViews();
}

async function addCommitment() {
  const result = await api(`/sessions/${state.activeSessionId}/narrative/commitments`, "POST", explicitParticipantPayload({
    commitment: $("commitmentText").value.trim(),
    failure: $("failureText").value.trim(),
    recovery: $("recoveryText").value.trim(),
    visibility_scope: selectedVisibility(),
  }));
  $("narrativeState").textContent = pretty(result);
  await refreshSession();
  await refreshGovernanceViews();
}

async function exportPrivacy() {
  const result = await api(`/sessions/${state.activeSessionId}/privacy/export`, "POST", explicitParticipantPayload({
    provenance: "ephux-local-ui",
  }));
  $("privacyState").textContent = pretty(result);
}

async function requestDeletion() {
  const result = await api(`/sessions/${state.activeSessionId}/privacy/deletion-requests`, "POST", explicitParticipantPayload({
    target_memory_id: $("memoryId").value.trim(),
    reason: $("privacyReason").value.trim() || "deletion requested",
    provenance: "ephux-local-ui",
  }));
  $("privacyState").textContent = pretty(result);
  await refreshSession();
  await refreshGovernanceViews();
}

async function placeLegalHold() {
  const result = await api(`/sessions/${state.activeSessionId}/privacy/legal-holds`, "POST", explicitParticipantPayload({
    target_memory_id: $("memoryId").value.trim(),
    reason: $("privacyReason").value.trim() || "legal hold requested",
    provenance: "ephux-local-ui",
  }));
  $("privacyState").textContent = pretty(result);
  await refreshSession();
  await refreshGovernanceViews();
}

async function proposeExternalAction() {
  const result = await api(`/sessions/${state.activeSessionId}/external-actions`, "POST", explicitParticipantPayload({
    connector_id: $("connectorId").value.trim(),
    operation: $("connectorOperation").value.trim(),
    target_locator: $("connectorTarget").value.trim(),
    account_label: $("connectorAccount").value.trim() || "sanitized-account",
    environment: $("connectorEnvironment").value,
    payload: {
      branch: $("connectorBranch").value.trim(),
      url: $("connectorUrl").value.trim(),
      headers: { Authorization: $("connectorAuthHeader").value.trim() },
    },
    expected_cost: $("connectorCost").value,
    visibility_scope: selectedVisibilityEnum(),
    verification_steps: ["verify fixture receipt"],
    rollback_steps: [$("connectorRollback").value.trim()].filter(Boolean),
    rollback_required: $("connectorAuthority").value !== "READ_ONLY",
  }));
  $("externalActionState").textContent = pretty(result);
  await refreshSession();
  await refreshConnectorViews();
}

async function approveExternalAction() {
  const proposalId = $("externalProposalId").value.trim();
  const result = await api(`/sessions/${state.activeSessionId}/external-actions/${proposalId}/approve`, "POST", explicitParticipantPayload({
    note: $("connectorApprovalNote").value.trim() || "approve connector action",
  }));
  $("externalActionState").textContent = pretty(result);
  await refreshSession();
  await refreshConnectorViews();
}

async function denyExternalAction() {
  const proposalId = $("externalProposalId").value.trim();
  const result = await api(`/sessions/${state.activeSessionId}/external-actions/${proposalId}/deny`, "POST", explicitParticipantPayload({
    reason: $("connectorApprovalNote").value.trim() || "deny connector action",
  }));
  $("externalActionState").textContent = pretty(result);
  await refreshSession();
  await refreshConnectorViews();
}

async function revokeExternalAction() {
  const proposalId = $("externalProposalId").value.trim();
  const result = await api(`/sessions/${state.activeSessionId}/external-actions/${proposalId}/revoke`, "POST", explicitParticipantPayload({
    reason: $("connectorApprovalNote").value.trim() || "revoke connector action",
  }));
  $("externalActionState").textContent = pretty(result);
  await refreshSession();
  await refreshConnectorViews();
}

async function executeExternalAction() {
  const proposalId = $("externalProposalId").value.trim();
  const result = await api(`/sessions/${state.activeSessionId}/external-actions/${proposalId}/execute`, "POST", {
    fixture_execute: true,
  });
  $("externalActionState").textContent = pretty(result);
  await refreshSession();
  await refreshConnectorViews();
}

async function submitConsciousnessPercept() {
  await api(`/sessions/${state.activeSessionId}/consciousness/percepts`, "POST", {
    percepts: [
      {
        topic: $("consciousnessPerceptTopic").value.trim(),
        content: $("consciousnessPerceptContent").value,
        source_type: $("consciousnessSourceType").value,
        confidence: Number($("consciousnessConfidence").value || "0.8"),
        salience: Number($("consciousnessSalience").value || "0.5"),
        purpose_relevance: Number($("consciousnessPurposeRelevance").value || "0.8"),
      },
    ],
  });
  await refreshSession();
}

async function submitConsciousnessPurpose() {
  await api(`/sessions/${state.activeSessionId}/consciousness/purposes`, "POST", {
    description: $("consciousnessPurpose").value.trim(),
    source_type: "explicit human request",
    source_detail: "ephux-local-ui",
    priority_weight: Number($("consciousnessPriority").value || "1"),
    priority_urgency: Number($("consciousnessUrgency").value || "0.2"),
  });
  await refreshSession();
}

async function setConsciousnessAttention() {
  await api(`/sessions/${state.activeSessionId}/consciousness/attention`, "POST", {
    lock_target_id: $("consciousnessAttentionTarget").value.trim(),
    reason: "manual-ui-lock",
  });
  await refreshSession();
}

async function runConsciousnessCycle() {
  const result = await api(`/sessions/${state.activeSessionId}/consciousness/cycles`, "POST", {
    claimed_capabilities: { "connector:github": true },
    tested_capabilities: {
      "connector:github": $("consciousnessCapabilityTested").value === "true",
    },
    allow_internal_action: $("consciousnessAllowInternal").value === "true",
  });
  $("consciousnessState").textContent = pretty(result);
  await refreshSession();
}

async function pauseConsciousness() {
  await api(`/sessions/${state.activeSessionId}/consciousness/pause`, "POST", { reason: "manual-ui-pause" });
  await refreshSession();
}

async function resumeConsciousness() {
  await api(`/sessions/${state.activeSessionId}/consciousness/resume`, "POST", { reason: "manual-ui-resume" });
  await refreshSession();
}

async function reviewConsciousness() {
  const result = await api(`/sessions/${state.activeSessionId}/consciousness/review`, "POST", {
    requested_by: "ephux-local-ui",
  });
  $("consciousnessState").textContent = pretty(result);
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
bind("retrieveMemory", retrieveMemory);
bind("promoteMemory", promoteMemory);
bind("demoteMemory", demoteMemory);
bind("pruneMemory", pruneMemory);
bind("addContribution", addContribution);
bind("addDecision", addDecision);
bind("addDisagreement", addDisagreement);
bind("addCommitment", addCommitment);
bind("exportPrivacy", exportPrivacy);
bind("requestDeletion", requestDeletion);
bind("placeLegalHold", placeLegalHold);
bind("refreshConnectors", refreshConnectorViews);
bind("proposeExternalAction", proposeExternalAction);
bind("approveExternalAction", approveExternalAction);
bind("denyExternalAction", denyExternalAction);
bind("revokeExternalAction", revokeExternalAction);
bind("executeExternalAction", executeExternalAction);
bind("submitConsciousnessPercept", submitConsciousnessPercept);
bind("submitConsciousnessPurpose", submitConsciousnessPurpose);
bind("setConsciousnessAttention", setConsciousnessAttention);
bind("runConsciousnessCycle", runConsciousnessCycle);
bind("pauseConsciousness", pauseConsciousness);
bind("resumeConsciousness", resumeConsciousness);
bind("reviewConsciousness", reviewConsciousness);
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
$("participantSelect")?.addEventListener("change", async () => {
  try {
    if (state.activeSessionId && currentToken()) {
      await refreshGovernanceViews();
      await refreshConnectorViews();
      await refreshConsciousnessViews();
    }
  } catch (error) {
    status(error.message, "danger");
  }
});
$("visibilitySelect")?.addEventListener("change", async () => {
  try {
    if (state.activeSessionId && currentToken()) {
      await refreshGovernanceViews();
      await refreshConnectorViews();
      await refreshConsciousnessViews();
    }
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
