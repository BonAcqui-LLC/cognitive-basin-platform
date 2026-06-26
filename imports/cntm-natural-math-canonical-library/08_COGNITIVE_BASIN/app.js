fetch("../outputs/dashboard_summary.json")
  .then(r => { if (!r.ok) throw new Error("Run operational_self/cli.py run-demo first"); return r.json(); })
  .then(d => {
    const st = d.operational_self_state || {};
    document.getElementById("stats").innerHTML = [
      ["Memories", (d.memories||[]).length],
      ["Core", (d.core_attractors||[]).length],
      ["Scars", (d.contradiction_scars||[]).length],
      ["Fog", (d.fog_regions||[]).length],
      ["Routes", (d.replay_routes||[]).length],
    ].map(([l,v]) => `<div class="stat-card"><div class="label">${l}</div><div class="value">${v}</div></div>`).join("");

    const nf = d.narrative_frame || {};
    document.getElementById("narrative").innerHTML = `<div class="card"><strong>${nf.current_identity_sentence||""}</strong><br>${nf.narrative_summary||""}</div>`;

    document.getElementById("attractors").innerHTML = (d.active_attractors||[]).slice(0,12).map(a =>
      `<div class="card"><span class="badge badge-${a.basin_region}">${a.basin_region}</span> ${a.label}<br>salience=${a.salience_score?.toFixed(2)} dist=${a.distance_from_reasoning_center?.toFixed(2)}</div>`
    ).join("") || "<div class='card'>No attractors</div>";

    const fog = (d.fog_regions||[]).map(f => `<div class="card"><span class="badge badge-fog">fog</span> ${f.label} — ${f.guard_status}</div>`).join("");
    const scars = (d.contradiction_scars||[]).map(s => `<div class="card"><span class="badge badge-scar">scar</span> ${s.claim_a} vs ${s.claim_b}</div>`).join("");
    document.getElementById("fog-scars").innerHTML = fog + scars || "<div class='card'>None</div>";

    document.getElementById("replay").innerHTML = (d.replay_routes||[]).map(r =>
      `<div class="card"><strong>${r.label}</strong><br>path: ${(r.memory_path||[]).length} memories<br>${r.recommended_next_action||""}</div>`
    ).join("") || "<div class='card'>No routes</div>";

    document.getElementById("retrieval").innerHTML = (d.retrieval_samples||[]).map(rs =>
      `<div class="card"><strong>${rs.query}</strong><br>${(rs.results||[]).slice(0,2).map(x => x.label + " (" + x.basin_region + ")").join("<br>")}</div>`
    ).join("") || "<div class='card'>No retrieval samples</div>";

    document.getElementById("audit").innerHTML = (d.audit_timeline||[]).slice(-10).reverse().map(a =>
      `<div class="card">${a.action} — ${a.target}</div>`
    ).join("");
  })
  .catch(e => document.body.insertAdjacentHTML("afterbegin", `<div class="error">${e.message}</div>`));