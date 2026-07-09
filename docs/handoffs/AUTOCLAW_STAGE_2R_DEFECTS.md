# AutoClaw Stage 2R Defects

Stage 2 is preserved here as an experimental implementation, not as a production-ready Natural Math extension layer.

## Directly Observed Runtime Defects

### Post-hoc phase dispatch

- In `imports/autoclaw-natural-math-workspace/03_EXPERIMENTS/extension_harness/local_adapter.py`, the harness calls `nm.run_step(...)` first and only then emits `AFTER_DECISION_FORMATION`, `AFTER_BIFURCATION_RESERVATION`, `AFTER_MOVEMENT_RESOLUTION`, `AFTER_PRESSURE_UPDATE`, and `AFTER_BONDING`.
- That means the named phase hooks are observing one completed frozen step after the fact rather than intervening at their real Natural Math phases.
- Stage 2R must introduce phase-accurate integration points or rename the surfaces to match reality.

### Behavioral hook declared but not operationally dispatched

- `imports/autoclaw-natural-math-workspace/03_EXPERIMENTS/extension_harness/protocol.py` declares `PROPOSE_LOCAL_MOVE_PREFERENCE`.
- `imports/autoclaw-natural-math-workspace/03_EXPERIMENTS/extension_harness/types.py` maps it to `propose_local_move_preference`.
- `imports/autoclaw-natural-math-workspace/03_EXPERIMENTS/extension_harness/local_adapter.py` does not dispatch that hook in the live step path.
- Stage 2R must wire the proposal hook into the actual local-choice point or explicitly leave it unsupported.

### Hook-result validation not enforced in runtime dispatch

- `imports/autoclaw-natural-math-workspace/03_EXPERIMENTS/extension_harness/hook_results.py` defines `validate_hook_result`.
- `imports/autoclaw-natural-math-workspace/03_EXPERIMENTS/extension_harness/local_adapter.py` currently records hook result types in `_dispatch(...)` but does not call `validate_hook_result` before accepting those results as runtime events.
- Existing tests prove the validator works in isolation; Stage 2R must make that contract active in the runner itself.

### State store present but not integrated into operational execution

- `imports/autoclaw-natural-math-workspace/03_EXPERIMENTS/extension_harness/state_store.py` defines `StateStore`.
- The operational runner path in `imports/autoclaw-natural-math-workspace/03_EXPERIMENTS/extension_harness/runner.py` builds a registry and provenance record but does not connect a persistent `StateStore` through the live execution flow.
- Stage 2R must integrate extension state explicitly while keeping frozen node state untouched and run isolation intact.

## Preserved Known Limitations From The Verified Handoff

These limitations were carried forward from the controlling transfer prompt and preserved AutoClaw handoff evidence. They should be treated as active warnings unless and until new executable evidence refutes them.

- Parts of proposal validation assume 2D object nodes rather than the full 3D Natural Math dictionary node structure.
- Extension object state may persist across runs if caller-owned extension instances are reused without a stricter reset boundary.
- Baseline hashes are declared syntactically but not fully enforced against the active frozen baseline.
- Some mode-equivalence reports overstate what was actually routed through the harness.

## Required Stage 2R Outcome

Stage 2R is complete only when:

1. hook timing matches real Natural Math phases or is honestly renamed,
2. runtime dispatch enforces hook-result contracts,
3. proposal hooks are either truly live or explicitly unsupported,
4. extension state is isolated and operationally integrated,
5. baseline/hash and mode-equivalence claims are backed by executable verification, and
6. historical reports are superseded without rewriting the original evidence.
