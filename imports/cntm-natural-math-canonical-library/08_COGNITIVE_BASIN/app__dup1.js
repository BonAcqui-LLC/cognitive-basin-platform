async function load() {
  const res = await fetch("../outputs/dashboard_summary.json");
  if (!res.ok) throw new Error("Run guardian_authority/cli.py run-demo first");
  return res.json();
}

function stats(data) {
  const el = document.getElementById("stats");
  const claims = data.authority_claims || [];
  const holds = claims.filter(c => c.guard_recommendation === "HOLD").length;
  el.innerHTML = [
    ["Sources", (data.authority_sources || []).length],
    ["Records", (data.authority_records || []).length],
    ["Claims", claims.length],
    ["Conflicts", (data.conflicts || []).length],
    ["HOLD", holds],
  ].map(([l, v]) => `<div class="stat-card"><div class="label">${l}</div><div class="value">${v}</div></div>`).join("");
}

function sourcesTable(data) {
  const rows = (data.authority_sources || []).map(s =>
    `<tr><td>${s.source_name}</td><td>${s.source_type}</td><td>${s.jurisdiction}</td><td>${s.license_status}</td><td>${s.version}</td></tr>`
  ).join("");
  document.getElementById("sources-table").innerHTML =
    `<table><thead><tr><th>Name</th><th>Type</th><th>Jurisdiction</th><th>License</th><th>Version</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function claimsTable(data) {
  const routes = data.citation_routes || [];
  const rows = (data.authority_claims || []).map(c => {
    const cr = routes.find(r => r.claim_id === c.claim_id) || {};
    return `<tr>
      <td>${c.text.substring(0, 60)}...</td>
      <td><span class="badge badge-${c.support_status === 'supported_within_scope' ? 'supported' : c.support_status}">${c.support_status}</span></td>
      <td><span class="badge badge-${c.guard_recommendation}">${c.guard_recommendation}</span></td>
      <td>${cr.scope_match ?? '—'}/${cr.jurisdiction_match ?? '—'}/${cr.version_match ?? '—'}</td>
    </tr>`;
  }).join("");
  document.getElementById("claims-table").innerHTML =
    `<table><thead><tr><th>Claim</th><th>Support</th><th>GUARD</th><th>Scope/Juris/Ver</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function conflictsList(data) {
  document.getElementById("conflicts-list").innerHTML = (data.conflicts || []).map(c =>
    `<div class="conflict-entry"><strong>${c.conflict_type}</strong> — ${c.record_a} vs ${c.record_b}<br>${c.notes || ''}</div>`
  ).join("") || "<p>No conflicts.</p>";
}

function audit(data) {
  document.getElementById("audit-timeline").innerHTML = (data.audit_timeline || []).slice(-15).reverse().map(a =>
    `<div class="audit-entry"><strong>${a.action}</strong> ${a.target}<br><small>${a.timestamp}</small></div>`
  ).join("");
}

load().then(d => { stats(d); sourcesTable(d); claimsTable(d); conflictsList(d); audit(d); })
  .catch(e => document.body.insertAdjacentHTML("afterbegin", `<div class="error">${e.message}</div>`));