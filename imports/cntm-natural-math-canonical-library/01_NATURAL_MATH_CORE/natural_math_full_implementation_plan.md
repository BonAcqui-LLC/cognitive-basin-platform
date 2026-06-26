# Natural Math Full Implementation Plan

Status: active working plan
Date: 2026-06-08

## Goal

Build one real, local-first Natural Math implementation that:

- runs deterministically;
- matches the strongest defensible parts of the `2.3`/`2.4` specification;
- exports analyzable morphology/state evidence;
- is honest about what is implemented, approximated, and still experimental;
- can be smoke-tested repeatedly without drama.

This is not the plan for a paper.
This is the plan for a working apparatus.

## Build Doctrine

One hope is not enough unless it becomes one baseline.

We should not keep treating every external AI repair as a candidate canonical simulator.
Instead:

1. Keep one canonical implementation target in this repo: `natural_math/`.
2. Treat external scripts from Grok, DeepSeek, ERNIE, Copilot, and others as donor branches.
3. Merge features intentionally, one subsystem at a time.
4. Re-smoke after every subsystem merge.
5. Pull the team back in for review only at defined checkpoints, not after every edit.

## Canonical Implementation Target

Canonical package root:

`C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\natural_math`

Authoritative executable target for this repo:

- `natural_math/lattice.py`
- `natural_math/state.py`
- `natural_math/decisions.py`
- `natural_math/energy.py`
- `natural_math/pressure.py`
- `natural_math/simulator.py`
- `natural_math/presets.py`
- `natural_math/export.py`

Optional CLI entry later:

- `tools/natural_math_run.py`

## Immediate Baseline Rule

Current safest external baseline:

`C:\Users\moop\Downloads\Articles on X.com\Natural Math\Natural_Math_Simulator_v1.2.py`

Current strongest donor branch:

`C:\Users\moop\Downloads\Articles on X.com\Natural Math\Grok_Natural_Math_Simulator_v1.2.py`

Current strongest document architecture:

`C:\Users\moop\Downloads\Articles on X.com\Natural Math\Natural Math Version 2.4 — Copilot.docx`

Use them like this:

- `Natural_Math_Simulator_v1.2.py` is the behavioral reference that currently reruns cleanly.
- `Grok_Natural_Math_Simulator_v1.2.py` is the first donor for code structure, CLI shape, invariant checks, and environment hooks.
- `2.4 — Copilot` is the donor for claim labeling and implementation-alignment framing, not automatic proof of correctness.

## What We Should Build First

The full implementation should be built in this order:

### Stage 1: Canonical Core Loop

Minimum target:

- exact `Node` / site state;
- global simulation state;
- deterministic seed handling;
- synchronous step loop;
- `EXTEND`, `SENSE`, `RESTRICT`, `CONSERVE`;
- energy spending and dissipation;
- trail update and decay;
- pressure accumulation;
- inactive-state detection.

Acceptance:

- a single closed-system run completes;
- no crash;
- repeatable output under fixed seed;
- smoke report includes active site counts, total energy, and halt step.

### Stage 2: Spatial Legibility

Add:

- integer lattice helpers;
- quadrance-based neighbor logic;
- conflict detection;
- inert-site blocking;
- obstacle contact;
- optional simple environment map.

Acceptance:

- no overlapping occupancy after update;
- contact pressure changes are visible in diagnostics;
- obstacle runs differ from empty-space runs in reproducible ways.

### Stage 3: Bifurcation Geometry

Add:

- spread-controlled child generation;
- bifurcation thresholds;
- parent/child bookkeeping;
- child survival energy floor checks.

Acceptance:

- bifurcation happens only under documented conditions;
- child directions are valid integer vectors;
- site counts and parent relations remain sane.

### Stage 4: Invariant and Evidence Layer

Add:

- explicit invariant checks;
- run summary object;
- JSON export;
- CSV step log;
- morphology export hooks compatible with Fractalish analyzer.

Acceptance:

- run can emit a machine-readable evidence package;
- invariant failures surface clearly instead of hiding in prose;
- no more “trust me” report lines.

### Stage 5: Reproduction Scaffold

Add conservatively:

- `REPRODUCE` state;
- independent forest IDs;
- offspring seed creation;
- energy transfer accounting;
- mutation hook on `P_bifurcate`;
- rolling efficiency approximation.

Acceptance:

- reproduction logic runs without breaking core invariants;
- all births are counted;
- all forest IDs are tracked correctly;
- closed-system runs still eventually reach inactivity in the tested slice.

### Stage 6: Spec-Heavy Reproduction Upgrade

Add later, after Stage 5 is stable:

- subtree-local `ExpansionEfficiency(p,t)`;
- recent descendant accounting;
- stronger population diagnostics;
- selection and persistence experiments;
- explicit distinction between validated and hypothesized outcomes.

Acceptance:

- code actually demonstrates what Appendix B claims;
- otherwise Appendix B stays marked as partial / research-active.

## Team Farming Strategy

Yes, we should farm work out.
But not by asking everybody to “fix Natural Math” at once.

Farm by subsystem.

### Good Team Tasks

1. Spatial indexing and neighbor search hardening
2. Invariant-check library
3. Environment / obstacle hooks
4. Reproduction accounting and forest lineage logging
5. Export/report layer
6. Benchmark harness
7. Determinism and seed reproducibility audit
8. Fractalish analyzer compatibility export

### Bad Team Tasks

1. “Rewrite the whole simulator”
2. “Make it full spec-complete”
3. “Prove the theorem in code”
4. “Polish everything”

Those produce dramatic output, but they muddy provenance and waste merge time.

## When To Pull The Team Back In

Use the team for checkpoint reviews only.

### Checkpoint A

After Stage 1 + 2:

- ask for smoke testing;
- ask for hidden crash detection;
- ask for invariant edge cases.

### Checkpoint B

After Stage 3 + 4:

- ask for geometry correctness review;
- ask for export/report criticism;
- ask whether the evidence package is actually useful.

### Checkpoint C

After Stage 5:

- ask for Appendix B mismatch review;
- ask whether reproduction code matches its written claims;
- ask for adversarial parameter cases.

### Checkpoint D

After Stage 6:

- ask for a hard credibility review;
- ask whether the spec still overclaims;
- ask what remains unsupported.

## What To Ignore For Now

Do not spend the first serious implementation pass on:

- polished UI;
- cloud deployment;
- giant visualization systems;
- speculative domain hooks;
- persistence mythology;
- marketing-ready terminology inflation.

## Recommended Merge Policy

When importing from external donor scripts:

1. copy the subsystem, not the whole file;
2. keep names stable inside `natural_math/`;
3. preserve a comment pointing to donor inspiration if useful;
4. rerun smoke tests immediately;
5. record what changed and what is still approximate.

## Concrete Next Build Step

Immediate next task:

Port the current real simulator logic into `natural_math/simulator.py` and supporting modules so the canonical implementation stops living only in standalone external scripts.

That means:

- migrate stable `Node` and simulator state structures;
- migrate the deterministic core loop;
- migrate energy/pressure/trail logic;
- add a minimal local runner script;
- produce one JSON or CSV evidence export;
- add smoke tests.

## Definition Of Success

We are succeeding if, at the end of the day, we have:

- one canonical local package implementation;
- one reproducible CLI run;
- one honest evidence export;
- one clear list of what is exact, approximate, and deferred;
- one disciplined lane for external team contributions.

Not:

- five impressive scripts;
- three contradictory documents;
- and one exhausted human trying to remember which one “really works.”
