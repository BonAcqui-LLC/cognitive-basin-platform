# Natural Math Version Lineage Map

Generated: 2026-06-23 T05:42 EDT
Authority: Natural Math v5 frozen integer base (SHA256: E5AB47D41B82F6AF573866BE637BF3B0054D96C7F45A613EC6CAE2124AD84C7B)

## Version Timeline

| Version | Date (approx) | Type | Authority | Code Status | Validation |
|---|---|---|---|---|---|
| v2.2 | early 2026 | Publication draft | Superseded | `Natural_Math_v2.2.1.py` (float) | None |
| v2.3 | early 2026 | Publication draft | Superseded | PDF/implementation-aligned doc | None |
| v2.4 | early 2026 | Publication draft | Superseded | Copilot-enhanced doc | None |
| v3.6 | mid 2026 | Executable spec | Predecessor | `v3_6_core.py` (float, ~350 lines) | 8/8 oracles (float) |
| v3.8 | mid 2026 | Scaling revision | Predecessor | `Natural_Math_v3.8.py` | None |
| v4 | mid 2026 | Crystal discovery | Historical | `melissa_crystal_grain_v4_clean.py` | seed42 output |
| v5 | 2026-06 | **FROZEN authoritative** | **CANONICAL** | Integer oracle runner (687 lines) + spec doc | **40/40** (25 int + 15 cluster) |
| v5.1 | 2026-06 | Developmental extension | Extension | In `Natural Math v5.1 - Experimental Baby AI Sandbox/` | First extension lane |
| v6 | late 2026 | Crystal growth variant | Research branch | `Natural_Math_Seed_And_Grow_Crystal_v6.py` | Unvalidated |
| v7.2 | late 2026 | Cluster energy network | Research branch | `Cluster Energy Network v7.2.1.py` | Unvalidated |

## Version Relationships

```
v2.2 → v2.3 → v2.4 (publication drafts, float-based)
                ↓
              v3.6 (executable spec, float, 8 oracles)
                ↓
              v3.8 (scaling revision)
                ↓
              v4 (Melissa crystal grain discovery, stick mechanism)
                ↓
              v5 (FROZEN, integer-only rewrite, 40/40 oracles) ← AUTHORITY
                ↓
              v5.1 (first developmental extension)
              v6 (crystal growth, research branch)
              v7.2 (cluster energy, research branch)
```

## Key Architectural Shift

v5 is NOT a refinement of v3.6. It is a **rewrite** that changed the fundamental numeric representation from floating-point to integer (milli-units). The entire gradient system, contact rules, energy costs, and validation were redesigned for exact integer reproducibility.

## Other Natural Math Branches

### Stick / Crystal Grain Mechanism (v4 lineage)
- **Purpose:** Discovered by Melissa — seed42 crystal formation with local growth rules
- **Source:** `melissa_crystal_grain_v4_clean.py`, `melissa_v4_seed42_output.txt`
- **Status:** Historical discovery, not canonical
- **Baby-AI role:** None yet. Could provide morphological diversity examples for later MCVA training.
- **Conflict with v5:** Different growth rules, no cluster benchmark, not integer-only

### Cluster Energy Network (v7.2)
- **Purpose:** Energy distribution network simulation with cluster dynamics
- **Source:** `Cluster Energy Network v7.2.1.py`
- **Status:** Research branch, unvalidated against v5 cluster benchmark
- **Baby-AI role:** None. v5 already has a validated cluster benchmark (Sections 18-22).
- **Conflict with v5:** Different cluster semantics, not validated

### Persistent Attractor + PEFP
- **Purpose:** Evolution Prize lane — persistent states with Construction A+/PEFP readout
- **Source:** `FractalishBuild\fractalish-ai\fractalish_ai\evolution_prize_validation\`
- **Status:** Evolution Prize work (FAILED prize thresholds, but mechanics functional)
- **Baby-AI role:** Later (Stage 7+). Relevant to Construction A+ integration.
- **Conflict with v5:** PEFP reads continuous natural_math states, not v5 integer states

### CNTM-Related Natural Math
- **Purpose:** Carbon Nanotube Morphology — Natural Math applied to CNT-like structures
- **Source:** CNTM canonical library lanes 04 and 05
- **Status:** Software simulation, not validated against v5
- **Baby-AI role:** None. CNTM is a separate substrate workbench, not the core mechanics layer.

## V5 Cluster Benchmark Relationship

The v5 cluster benchmark (Sections 18-22) is NOT the same as the v7.2 Cluster Energy Network. The v5 cluster is:
- Part of the frozen v5 spec
- Has 15/15 validated oracle fixtures (initialization, metrics, actions, damage, full runs)
- Is open-system (resource absorption adds external energy)
- Is primarily a cluster resilience/repair test, not an energy optimization benchmark

## Frozen v5.1 Extension Lane

v5.1 is specifically designated in the project decision as the "first separately versioned developmental extension." The v5.1 directory in `Natural Math v5.1 - Experimental Baby AI Sandbox\` contains:
- Consolidated paper
- Test results
- Oracle fixtures and runners
- Scale gate evidence (Gates 1-8)

These should be reviewed in Stage 2 (extension harness) but not confused with v5 frozen base.
