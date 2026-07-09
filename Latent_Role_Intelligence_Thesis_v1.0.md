# Latent Role Intelligence and Sparse Basin Realization
## A Compute-Bounded Thesis for Fractalish / Cognitive Basin Architectures

**Version 1.0 — Canonical Working Thesis**  
**June 26, 2026**

> **Canonical thesis:** A human-scale cognitive basin should contain many richly specified role intelligences, but realize only a sparse subset at any moment. The persistent unit is a compact Role Kernel; the expensive agentic process is reconstructed only when a ternary activation condition requires it.

## Abstract

The Cognitive Basin model originally treated broad faculties such as perception, rigor, affect, reasoning, continuity, and action governance as major modules. That abstraction is insufficient for human-scale nuance. Each apparent faculty is better understood as a federation of persistent, purpose-built role intelligences: contradiction, care, threat, novelty, source continuity, causal coherence, fairness, curiosity, identity preservation, temporal ordering, and many others.

A direct implementation of dozens or hundreds of continuously active agents would be computationally unmanageable. This thesis resolves the conflict by separating cognitive capacity from realized cognitive expenditure. A role remains persistent as a compact Role Kernel containing its fixed telos, relevance signature, memory pointers, activation conditions, authority boundaries, and unresolved holds. It becomes a full Role Process only when the shared basin emits a relevant event and a ternary gate returns ADVANCE. After intervention, the process compresses its durable state into a Role Residue and terminates.

The resulting architecture is code-dense but execution-sparse. It combines shared encoding, hierarchical routing, ternary activation, event-sourced basin state, reconstructive memory, typed inter-role communication, and hard compute governance.

## Canonical Thesis Statement

> A human-scale Cognitive Basin should be designed as a large ecology of latent, purpose-built role intelligences sharing a common substrate. Rich cognitive capacity may remain persistent in compact kernels, while expensive agentic realization occurs only through sparse, ternary, event-driven activation. The system remains continuously recoverable rather than continuously instantiated.

## 1. The Design Problem

Broad modules such as ATAL, RIGOR, PERCEPT, affect, logic and reasoning, memory, and safety were useful as early architectural categories. They were not yet sufficient cognitive mechanisms. Human perception is not one operation; human rigor is not one verifier; affect is not one scalar; and reasoning is not one general process.

The revision is not to discard the macro-modules. It is to demote them from individual minds to federations: namespaces, routing domains, and governance boundaries for narrower role intelligences.

A naïve design in which every role remains an always-running agent would multiply tokens, duplicate context, create drift, and make internal committee traffic more expensive than useful cognition. The resolution is reconstructive sparsity: preserve the role compactly and instantiate it only when relevance warrants.

## 2. Foundational Distinctions

- **Code density is not compute density.** The system may define hundreds of roles while activating only a few.
- **Capacity is not realization.** Latent cognitive repertoire is not current cognitive expenditure.
- **Persistence is not residency.** Continuity can be reconstructed from kernel, residue, memory, and current context.
- **HOLD is not inactivity.** It stores a live dependency and a release condition, then permits sleep.
- **Role is not assignment.** A role is purpose-built around a fixed concern; it is not a generic agent temporarily prompted.
- **Shared substrate is not independent minds.** Roles share encoders, memory, tools, entity models, and simulation primitives.

`N_defined_roles >> N_active_roles(t)`

## 3. Formal Definitions

### 3.1 Role Intelligence

`R_i = (τ_i, Ω_i, φ_i, M_i, Π_i, Θ_i, Γ_i)`

- `τ_i`: fixed telos.
- `Ω_i`: observable inputs and event subscriptions.
- `φ_i`: role-specific representation and feature selection.
- `M_i`: role memory and retrieval policy.
- `Π_i`: evaluation and intervention policy.
- `Θ_i`: activation, escalation, hold, and release conditions.
- `Γ_i`: authority boundaries and permitted outputs.

### 3.2 Role Kernel

The always-available compact representation: telos, relevance signature, wake and inhibition conditions, memory pointers, compact residue, authority limits, and model or adapter identifiers.

### 3.3 Role Process

The temporary agentic realization of the kernel. It receives a minimal relevant basin neighborhood, retrieved memory, the trigger event, and a compute budget. It reasons, writes a typed report, updates residue, and terminates.

`Role Kernel --relevant event--> Role Process --report--> Role Residue`

### 3.4 Role Residue

Compact durable state for future reconstruction: unresolved concerns, learned sensitivities, recent interventions, calibrated thresholds, and links to relevant episodes.

### 3.5 Basin

A shared event-sourced coordination field containing entities, propositions, hypotheses, goals, threats, holds, candidate actions, provenance, role reports, conflicts, predictions, and outcomes. It is neither one executive agent nor an agent chat room.

## 4. Core Architectural Laws

1. **Dense Capacity, Sparse Realization.**
2. **Encode Once, Route Many.**
3. **Reconstruct, Do Not Reside.**
4. **HOLD Is a Subscription.**
5. **Typed Changes Beat Prose Traffic.**
6. **Authority Is Contextual.**
7. **Compute Is Governed.**
8. **Telos Is Stable, Strategy Is Learnable.**

## 5. Ternary Activation

`g_i(e_t, B_t) ∈ { INHIBIT (-1), HOLD (0), ADVANCE (+1) }`

- **INHIBIT:** irrelevant, suppressed, or barred.
- **HOLD:** potentially relevant but not yet justified; store dependencies and remain dormant.
- **ADVANCE:** instantiate the Role Process at the lowest sufficient compute level.

A HOLD object records owner, reason, required evidence, wake conditions, urgency, and expiry. It is an active subscription rather than continuing inference. This suppresses unsupported downstream branches and reduces compensatory compute.

## 6. Shared Substrate and Hierarchical Routing

`x_t --shared encoder--> e_t`

The shared event representation contains semantics, entities, changes, provenance, novelty, affect markers, action implications, and uncertainty.

Activation proceeds recursively:

`Event → Macro-family → Subfamily → Role Kernel → Role Process`

Compute ladder:

- **Level 0:** reflex gate.
- **Level 1:** role probe.
- **Level 2:** role cognition.
- **Level 3:** temporary deliberative assembly.

## 7. Reconstructive Role Cognition

`R_i(t) = Reconstruct(K_i, ρ_i, M_i*, B_t*, e_t, budget_i)`

The role reconstructs from its kernel, residue, retrieved memory, relevant basin slice, trigger, and budget. It does not require its full lifetime transcript. Durable outputs are a typed report and updated residue.

## 8. Basin Arbitration and Governance

The basin stores typed objects, not endless role conversations. Arbitration is contextual, not majority voting:

`Decision(a) = f(advance pressure, inhibition pressure, active holds, authority, evidence, consequence, reversibility)`

Irreversible actions require stricter hold release than reversible hypotheses. Governance is also federated through metacognitive roles that detect excessive agreement, role monopolies, stale assumptions, circular consultation, budget overrun, and improper hold release.

## 9. Compute Thesis

Naïve:

`C_naive ≈ N_roles × C_full-agent`

Sparse:

`C_t = C_shared-encoding + N_roles × C_cheap-gate + Σ(i∈A_t) C_activated-role_i`

The thesis is viable only when cheap gating is much less expensive than full cognition and `|A_t| << N_roles`.

This is an empirical claim. Measure activation precision and recall, reconstruction overhead, latency, energy, token use, committee depth, cache reuse, and task integrity. Reject the thesis if overhead erases the gain.

## 10. Revised Module Status

- **PERCEPT** becomes a federation of continuity, segmentation, novelty, anomaly, source identity, temporal ordering, occlusion, multimodal consistency, salience, affordance, and viewpoint roles.
- **RIGOR** becomes a federation of contradiction, provenance, unsupported inference, counterexample, falsifiability, causal validity, scope error, category error, confound detection, and uncertainty preservation.
- **AFFECT** becomes a federation of threat, attachment, trust, care, fairness, grief, shame, belonging, disgust, curiosity, frustration, fatigue, loss aversion, awe, and social consequence.
- **ATAL** remains a macro-family but must be decomposed into explicit permanent roles rather than expanded as one monolith.
- **MEMORY** and **ACTION** become federations with explicit commitment, permission, reversibility, and audit roles.

## 11. Implementation Program

### Phase 0 — Formalization
Create canonical ontologies, schemas, ternary semantics, role contracts, compute budgets, and versioned registries.

### Phase 1 — Minimal Reference Basin
Implement roughly 12–18 roles, including perceptual continuity, novelty/anomaly, provenance, contradiction, counterexample, causal coherence, threat, care, curiosity, goal continuity, memory consistency, consequence simulation, unresolved-context hold, budget regulation, and conflict auditing.

### Phase 2 — Sparse Runtime
Build shared encoding, hierarchical routing, reconstruction, typed basin storage, budget governance, and replay.

### Phase 3 — Learning and Consolidation
Calibrate gates, learn strategies without telos drift, consolidate residue, detect duplicate and missing roles, and introduce model-size escalation.

### Phase 4 — Multimodal Extension
Expand only after the textual basin is auditable and compute-stable.

## 12. Evaluation and Falsification

Required measures include defined-role capacity, realized activation, activation precision and recall, HOLD utility, reconstruction fidelity, compute efficiency, decision integrity, recoverability, and auditability.

Compare against:

- one general-purpose agent;
- a flat multi-agent ensemble;
- mixture-of-experts without persistent residue;
- binary proceed/reject architecture;
- shared model prompts without event-sourced basin objects.

Revise or reject the thesis if routing misses critical roles, HOLD causes stagnation, reconstruction drifts, typed reports destroy necessary nuance, activation storms become normal, or total overhead exceeds simpler systems at equal reliability.

## 13. Team Structure

This is ultimately a team project spanning architecture, distributed runtime, representations, evaluation, interpretability, safety, and domain role design. The ontology and contracts must be stabilized before large-scale delegation. The first reference implementation can remain small but must be team-buildable through registries, schemas, tests, and independent role validation.

## 14. Risks and Open Questions

Principal risks: router blindness, activation storms, role capture, residue drift, stale HOLD accumulation, committee recursion, shared-encoder bias, false efficiency, overformalization, and anthropomorphic overreach.

Open questions include the minimum sufficient kernel, authority representation, universal versus instance-specific roles, safe learned activation, affective persistence, assembly triggers, biological mapping, and scaling laws relating role diversity to realized activation and integrity.

## 15. Canonical Summary

Many latent Role Kernels + one shared substrate + sparse ternary activation + temporary Role Processes + reconstructive memory = a compute-bounded Cognitive Basin capable of increasing nuance without requiring all cognition to run at once.

## Appendix A — Role Kernel Contract

```yaml
role_id:
version:
family:
fixed_telos:
authority_scope:
subscribed_event_types:
relevance_signature:
inhibition_conditions:
hold_conditions:
wake_conditions:
escalation_conditions:
required_context:
memory_queries:
shared_tools:
specialist_adapter:
default_compute_level:
maximum_compute_budget:
consultation_permissions:
report_schema:
residue_schema:
termination_conditions:
audit_requirements:
telos_lock:
```

## Appendix B — Qwen Handoff Protocol

Provide this thesis as canonical working reference. Require Qwen to:

1. Restate the architecture neutrally before critiquing it.
2. Identify contradictions with earlier Cognitive Basin materials.
3. Label findings as ACCEPTED, QUESTIONED, CONTRADICTED, or OPEN.
4. Produce an implementation delta covering schemas, runtime, tests, migration, and risk.
5. Preserve the fixed meanings of Role Kernel, Role Process, Role Residue, Basin, and HOLD.
6. Avoid invented project history; unknowns remain unknown.
7. Treat this as a working thesis subject to empirical falsification, not doctrine beyond revision.
