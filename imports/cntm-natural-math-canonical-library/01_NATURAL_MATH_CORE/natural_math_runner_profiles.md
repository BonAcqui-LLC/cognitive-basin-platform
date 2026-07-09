# Natural Math Runner Profiles

Status: current canonical runner guide
Date: 2026-06-08

## Purpose

The canonical Natural Math runner now supports named profiles so the package can demonstrate different behaviors without manual parameter hunting.

Runner:

`C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\tools\natural_math_run.py`

Canonical package:

`C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\natural_math`

## Quick Start

Default:

```bash
python tools/natural_math_run.py
```

The default profile is currently:

`bifurcation-demo`

That choice is deliberate. It demonstrates real branch splitting in the canonical package.

## Profiles

### `smoke`

Purpose:

- closed-system inactive-state baseline
- stable regression target
- theorem-adjacent smoke test lane

Command:

```bash
python tools/natural_math_run.py --profile smoke
```

What it currently shows:

- deterministic freeze
- no reproduction births
- no branch splitting
- explicit invariant checks

Use it when:

- verifying that the package still reaches inactivity
- checking that refactors did not break the baseline
- collecting the simplest comparison output for reviewers

### `growth-demo`

Purpose:

- demonstrate real `EXTEND`
- show that the package can produce child growth rather than only repeated `SENSE`

Command:

```bash
python tools/natural_math_run.py --profile growth-demo
```

What it currently shows:

- real extend decisions
- single-child extension events
- reproduction activity under the current conservative scaffold

Use it when:

- verifying that gradients and child creation are alive
- checking that event logging captures real growth behavior

### `bifurcation-demo`

Purpose:

- demonstrate real branch splitting in the canonical package
- serve as the current headline demo profile

Command:

```bash
python tools/natural_math_run.py --profile bifurcation-demo
```

What it currently shows:

- real extend decisions
- real bifurcation events
- one single-child extension
- one reproduction birth in the current tuned scenario
- closed-system freeze after the demo run

Use it when:

- showing that the package now supports actual branch splitting
- comparing future bifurcation logic changes
- checking whether obstacle/pressure logic still routes into a split

### `obstacle-growth`

Purpose:

- simple obstacle-aware growth lane
- intermediate diagnostic between plain growth and the full bifurcation demo

Command:

```bash
python tools/natural_math_run.py --profile obstacle-growth
```

Use it when:

- checking obstacle blocking behavior
- validating contact-pressure changes
- testing event logs around constrained movement

## CLI Overrides

You can override profile defaults with runner flags:

```bash
python tools/natural_math_run.py --profile bifurcation-demo --max-steps 200 --out tmp/nm_demo
```

Available useful overrides:

- `--max-steps`
- `--seed`
- `--initial-energy`
- `--p-bifurcate`
- `--e-reproduce`
- `--eta-reproduce`
- `--sigma-mutate`
- `--external-input`
- `--obstacles`
- `--out`

## Exports

If `--out` is provided, the runner currently writes:

- `natural_math_summary.json`
- `natural_math_history.csv`
- `natural_math_events.csv`

## What The Profiles Are Not

These profiles are demonstrations and regression anchors.

They are not:

- full Appendix B validation
- proof that every written theorem claim has been reproduced in code
- domain-specific scientific validation

## Recommended Review Use

For future hardening rounds:

1. run `smoke`
2. run `growth-demo`
3. run `bifurcation-demo`
4. compare event totals, freeze step, and validation flags

That gives reviewers three concrete lanes:

- inactive-state baseline
- child-growth lane
- branch-splitting lane

## Companion Files

- [README.md](C:\Users\moop\Downloads\Articles%20on%20X.com\Fractalish.com\README.md)
- [natural_math_full_implementation_plan.md](C:\Users\moop\Downloads\Articles%20on%20X.com\Fractalish.com\docs\natural_math_full_implementation_plan.md)
