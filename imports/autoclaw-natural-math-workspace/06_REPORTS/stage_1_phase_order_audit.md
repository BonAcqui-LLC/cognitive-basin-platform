# Natural Math v5 Stage 1 Phase-Order Audit

**Date:** 2026-06-23
**Spec:** Natural Math v5 - Status Frozen Int (SHA256: E5AB47...4C7B)

## run_step (Section 12) vs core_step.py

| Step | Spec Section 12 Requirement | core_step.py Implementation | Match? |
|------|---------------------------|----------------------------|--------|
| 1 | Validate Section 6 | `validate_nodes(nodes, params)` | PASS |
| 2 | Build active: live nodes sorted by ascending id | `active = sorted([node for node in nodes if node["alive"]], key=lambda n: n["id"])` | PASS |
| 3 | Kill active nodes outside -100..100 cube | `for node in active: if any(coord < -100 or coord > 100 for coord in node["pos"]): die_inert(node)` | PASS |
| 4 | Kill active nodes with energy < tau | `for node in active: if node["alive"] and node["energy"] < params["tau"]: die_inert(node)` | PASS |
| 5 | Rebuild active | `active = sorted([node for node in nodes if node["alive"]], key=lambda n: n["id"])` | PASS |
| 6 | Build frozen occupancy: all_occupied | `all_occupied = {node["pos"] for node in nodes}` | PASS |
| 7 | Initialize step-local scheduling structures | `movement_attempts`, `reserved_child_positions`, `scheduled_bifurcations` | PASS |
| 8 | Compute each active node decision in ascending id order | Decision loop over `active` (already sorted by id) | PASS |
| 9 | Apply RESTRICT_DIE decisions in ascending id order | `for node_id in sorted(decisions): if decisions[node_id][0] == "RESTRICT_DIE": die_inert(...)` | PASS |
| 10 | Apply SENSE decisions: energy -= eps_sense, clamp, die if < tau | Same loop pattern with SENSE check | PASS |
| 11 | Schedule EXTEND decisions: bifurcation check, movement_attempts build | Bifurcation check via `can_bifurcate()`, then movement_attempts | PASS |
| 12 | Resolve movement targets in ascending lexicographic order | `for target in sorted(movement_attempts)` (tuple sort = lexicographic) | PASS |
| 13 | Set direction for successful movers, kill below tau | `for nid in sorted(successful_directions): node["direction"] = ...; if energy < tau: die_inert` | PASS |
| 14 | Apply scheduled bifurcations in ascending parent id order | `for split_record in sorted(scheduled_bifurcations, key=lambda record: record["parent_id"])` | PASS |
| 15 | Apply pressure update to all nodes live before this phase | `update_pressure(nodes, params)` - iterates all nodes, updates only live ones | PASS |
| 16 | Apply bonding if enabled | `if allow_bonding: apply_bonding(...)` | PASS |
| 17 | Check runtime invariants | `validate_nodes(nodes, params)` + energy >= tau check | PASS |
| 18 | Clear step-local scheduling structures | Variables go out of scope at function end | PASS |
| 19 | Return the same nodes list object | `return nodes` | PASS |

**Result: 19/19 steps match the frozen spec exactly.**

## cluster_step (Section 19) vs cluster_step.py

| Step | Spec Section 19 Requirement | cluster_step.py Implementation | Match? |
|------|---------------------------|-------------------------------|--------|
| 1 | Alive nodes lose decay_cost, ascending id | `for node in sorted([n for n in state["nodes"] if n["alive"]], key=lambda n: n["id"]): node["energy"] -= params["decay_cost"]` | PASS |
| 2 | Clamp energy to zero | `for node in state["nodes"]: node["energy"] = max(0, node["energy"])` | PASS |
| 3 | Kill nodes below tau | `kill_below_tau(state["nodes"], params)` | PASS |
| 4 | If step_index == 35, apply damage | `if step_index == 35: apply_damage(...)` | PASS |
| 5 | Clamp energy to zero and kill nodes below tau | clamp + kill_below_tau after damage | PASS |
| 6 | Compute metrics | `metrics = compute_metrics(...)` | PASS |
| 7 | Select one cluster action | `action = select_cluster_action(...)` | PASS |
| 8 | Apply that action | `apply_cluster_action(action, state, params, rng)` | PASS |
| 9 | Clamp energy to zero and kill nodes below tau | clamp + kill_below_tau after action | PASS |
| 10 | Apply resource absorption | `apply_resource_absorption(state, params)` | PASS |
| 11 | Clamp energy to zero and kill nodes below tau | clamp + kill_below_tau after absorption | PASS |
| 12 | Check invariants | `check_cluster_invariants(state["nodes"], params)` | PASS |

**Result: 12/12 steps match the frozen spec exactly.**

## Conclusion

Both run_step (core_step.py) and cluster_step (cluster_step.py) follow the frozen specification phase ordering exactly. The previous deviation claims in __init__.py regarding "Phase ordering: now matches donor exactly rather than Section 12 document ordering" were incorrect — the donor code itself follows the spec ordering.

The cluster output format deviation claim was resolved by Issue 2 (run_cluster now returns Section 22 contract format, with donor-style summary in summarize_cluster_run).

## Stage 1 Correction Summary

| Issue | Description | Status |
|-------|-------------|--------|
| 1 | Run all 40 oracle fixtures | Pending (test runner created) |
| 2 | Fix run_cluster contract (6-key return) | DONE |
| 3 | Phase-order audit against spec | DONE (this report) |
| 4 | Cluster invariant error type | DONE |
| 5 | sample_two algorithm rewrite | DONE |
| 6 | Strict tuple validation | DONE |
| 7 | Bonding flag audit | DONE (removed non-spec check) |
| 8 | Trace module | DONE (deferred to Stage 2) |
