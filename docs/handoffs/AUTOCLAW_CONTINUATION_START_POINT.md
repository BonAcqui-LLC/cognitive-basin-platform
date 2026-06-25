# AutoClaw Continuation Start Point

## Imported Lineage

- Imported source repository: `C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE`
- Imported source branch: `main`
- Imported source HEAD: `ef0d0b6b0ae1fea0f035fc2a36bffe75f86306f9`
- Imported subtree prefix: `imports/autoclaw-natural-math-workspace/`
- Preserved frozen reference tag target: `natural-math-v5-reference-1.0` -> `28ffa5974b5fd157982f36fdb1189ac9d1fb6acb`
- Verified frozen Natural Math source SHA256: `E5AB47D41B82F6AF573866BE637BF3B0054D96C7F45A613EC6CAE2124AD84C7B`
- Preserved external handoff ZIP SHA256: `758F59126E14743ADEEF9DC0097043F891AA239774DF185C950D03FA7688198C`

## Verified Current Stage Status

- Stage 0: reports only
- Stage 1: implemented
- Stage 1.1: implemented
- Stage 2: implemented but operationally partial
- Stage 2R: required next repair tranche
- Stage 3: not implemented

## Authority And Mutation Boundaries

- The imported subtree preserves the committed AutoClaw history and must remain distinguishable from the existing Cognitive Basin platform runtime.
- The live AutoClaw source worktree currently has uncommitted generated-file deltas in:
  - `05_RESULTS/extension_harness/deterministic_mode_comparison.json`
  - `05_RESULTS/extension_harness/original_oracle_mode_comparison.json`
  - `06_REPORTS/stage_2_performance_report.md`
- Those uncommitted deltas were not imported into this repository. The preserved authority for this tranche is the committed six-commit AutoClaw lineage ending at `ef0d0b6b0ae1fea0f035fc2a36bffe75f86306f9`.
- Files that should be treated as frozen or provenance-bearing:
  - `imports/autoclaw-natural-math-workspace/02_REFERENCE_IMPLEMENTATION/*`
  - `imports/autoclaw-natural-math-workspace/05_RESULTS/*` historical evidence
  - `imports/autoclaw-natural-math-workspace/06_REPORTS/*` historical evidence
  - `docs/provenance/autoclaw/*`

## Verified Next Valid Task

The next valid AutoClaw engineering task is:

`Stage 2R Natural Math-specific harness repair`

That repair scope is:

1. Move local phase hook dispatch to the actual Natural Math phases rather than post-hoc observation of a completed frozen step.
2. Make `PROPOSE_LOCAL_MOVE_PREFERENCE` operationally dispatchable at the intended integration point.
3. Enforce `validate_hook_result` during runtime dispatch rather than relying on tests and helper utilities alone.
4. Correct proposal validation assumptions that still flatten or simplify Natural Math node structure.
5. Integrate `StateStore` into operational runners without contaminating frozen node state or cross-run isolation.
6. Tighten baseline-hash and mode-equivalence claims so reports match what the harness truly exercised.

## What Must Not Happen Next

- Do not silently present Stage 2 as production-ready.
- Do not merge Stage 2 harness behavior into the active platform runtime without a separate reviewed integration tranche.
- Do not bypass the frozen v5 reference semantics merely because the harness adds more surface area.
- Do not treat Local Flow Trail Memory or later Cognitive Basin layers as already implemented inside the imported AutoClaw workspace.
