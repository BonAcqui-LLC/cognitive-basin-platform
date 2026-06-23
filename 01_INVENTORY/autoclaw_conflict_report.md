# AutoClaw Conflict Report

Generated: 2026-06-23 T03:59 EDT

## Documented Conflicts

Per [Known Conflicts](C:\_MASTER_LIBRARY\00_CONTROL\06_KNOWN_CONFLICTS.md):

### CONFLICT-001: Natural Math v5 Frozen vs v5.1 Experimental-Extension Work
- **Status:** UNRESOLVED (structural, not adversarial)
- **Description:** Natural Math frozen v5 base must remain distinct from v5.1 experimental-extension work. The library preserves both tracks as separate lanes. The frozen v5 integer base is the non-negotiable mechanics authority.
- **Impact on development:** Extensions must be separately versioned. No silent merging of v5.1 ideas into v5 frozen base.

### CONFLICT-002: HOLD Enum/Semantic Boundary
- **Status:** RESOLVED (by governance)
- **Description:** HOLD is a runtime or decision state in the Fractalish/Cognitive Basin stack. It is not the same enum or contract as Natural Math `SENSE`. The library has documented this boundary explicitly via `mcva_gate_hold.md` and `hold.html`.
- **Impact on development:** Any code that handles states must treat HOLD and SENSE as separate, non-overlapping concepts.

### CONFLICT-003: Public vs Private Fractalish Release Materials
- **Status:** UNRESOLVED (environmental)
- **Description:** Public Fractalish release materials (`fractalish_public_site_v1.2`) do not necessarily equal the current private implementation baselines (`provider-sandbox-codex`, `ephux-local-integration-codex`).
- **Impact on development:** Public site materials carry weaker authority (Level 5). Private code baselines carry implementation authority (Level 4). When they diverge, the private baselines take precedence.

### CONFLICT-004: Guardian Materials - Canonical vs Provisional
- **Status:** UNRESOLVED (structural)
- **Description:** Guardian and Guardian Intake material exists both as canonical summaries (`guardian_intake_summary.json`) and as broader conceptual/provisional white papers (`Guardian Intake Gateway White Paper.docx`). They should not be merged silently.
- **Impact on development:** Canonical summary is Level 3; white paper is Level 4. When building, consult canonical first, white paper for context.

### CONFLICT-005: T81 Foundation Scope
- **Status:** UNRESOLVED (scoping)
- **Description:** The T81 codebase is substantial and relevant to ternary and activation-adjacent infrastructure, but it is supporting infrastructure rather than the primary Natural Math or Cognitive Basin authority. It should not be mistaken for a primary authority.
- **Impact on development:** T81 is reference/cross-check material, not a governing authority for this project.

## Readiness Classification

- Overall library readiness: **READY**
- Quarantine: **empty** (all quarantine buckets are empty directories)
- Missing material count: **0**
- All 5 repository snapshots: **verified Git provenance**

## Evidence Totals

| Status | Count |
|---|---|
| VERIFIED | 33 |
| DUPLICATE VERIFIED | 3 |
| PRESENT BUT NOT LISTED IN PROVENANCE | 14 |
| QUARANTINED | 0 |
| MISSING | 0 |

## Warnings

1. **Activation-native code baseline is documentation-only.** No dedicated runnable activation-native code baseline was positively located in the searched roots. The `15_ACTIVATION_ARCHITECTURE\ACT-001` workspace contains `core_runtime.py` and `minimal_runtime_spec.md` but these point to external canonical sources (`C:\Users\moop\FractalishBuild\fractalish-ai\`) that are not included in this library.
2. **14 evidence items present but not in provenance.** These are artifacts found in the library but not explicitly tracked in the formal provenance chain. They include manifest files, compressed archives, and duplicate result files.
3. **Provider sandbox codex branch has uncommitted changes.** The `provider-sandbox-codex` snapshot has `clean: false` with 1 untracked file (`pr_body_provider.txt`). This does not affect code integrity but should be noted.
4. **Natural Math stick repo has uncommitted changes.** The `natural-math-stick` snapshot has `clean: false` with 1 untracked file (`natural-math-stick.zip`). This does not affect code integrity but should be noted.
