# Fractalish AI v0.1

Fractalish AI v0.1 is a local-first prototype for process-aware, morphology-aware, state-disciplined AI infrastructure. It integrates Natural Math as a local bounded process engine, Fractalish / MCVA as a morphology readout and uncertainty-preserving classification layer, and Cognitive Basin Core as a traceable, stateful, ternary-gated reasoning-state runtime.

Natural Math generates process. Fractalish reads the shape left by process. Cognitive Basin preserves reasoning state across process.

## What it is

- A traceable, stateful, ternary-gated cognition simulator
- Local-first — no network required
- Natural Math v3.6 core (trunk) + MCVA morphology readout + Cognitive Basin guard spine
- JSON decision records you can inspect, diff, and carry forward
- Maze benchmark sandbox (controlled benchmark, not a grand claim)

## What it is not

- Not consciousness
- Not an agent army
- Not a chatbot skin
- Not medical, legal, financial, or disaster-prediction software
- Not proof of intelligence or AGI

State discipline before scale. HOLD before false closure. Operator sovereignty always.

## Three layers

| Layer | Role |
|-------|------|
| **Natural Math** | Bounded local process engine (growth / pressure / bifurcation) |
| **Fractalish / MCVA** | Morphology readout: MCVA / HOLD / AMCVA |
| **Cognitive Basin Core** | PERCEPT → ATAL → RIGOR → CIRCUIT → GUARD → SERA → SessionGlyph |

## Command checklist

Run from `C:\Users\moop\FractalishBuild\fractalish-ai` (Python 3.10+, stdlib only):

```bash
python examples/demo_natural_math.py
python examples/demo_natural_math_v3_6_core.py
python examples/demo_mcva_gate.py
python examples/demo_activation.py
python examples/demo_full_runtime.py
python examples/demo_natural_math_attractor_bias.py
python examples/demo_natural_math_goal_directed_v3_8.py
python examples/demo_generate_investor_packet.py
python examples/demo_1_false_continuity.py
python examples/demo_2_contradiction_scar.py
python examples/demo_3_recovery_route.py
python examples/demo_integrated_basin_morphology.py
python experiments/grok_sandbox/benchmark/run_maze_benchmark.py
python experiments/grok_sandbox/maze/maze_runner.py
python experiments/cognitive_basin_workbench/run_workbench.py
python experiments/cognitive_basin_sim_v1/run_simulation.py
python -m pytest -q
```

## Quick start

```bash
cd C:\Users\moop\FractalishBuild\fractalish-ai
python examples/demo_activation.py
python examples/demo_1_false_continuity.py
python examples/demo_integrated_basin_morphology.py
python -m pytest -q
```

Preview the local demo page:

```bash
python -m http.server 8080
# open http://localhost:8080/public/index.html
```

## Outputs

- `outputs/` — demo summaries (mostly gitignored; regenerate via demos)
- `demo_outputs/` — Cognitive Basin demo decision records
- `experiments/grok_sandbox/outputs/` — maze benchmark summaries and sample traces

## Natural Math canon

- **Trunk:** v3.6 core (`fractalish_ai/natural_math/v3_6_core.py`) — 8/8 oracles required
- **Grid demo:** `demo_natural_math.py` — memoryless vs memory-enabled comparison
- **Experimental branch:** v3.8 goal layer and attractor bias — separate, not core, not proof

## Guardian Intake Gateway v0.1

Local-first zero-trust intake membrane — quarantine, scan, sanitize, lifecycle-tag, and bridge to ReceptorEvent before Cognitive Basin. No cloud, no network, stdlib only.

```bash
python guardian/cli.py run-demo
python guardian/cli.py purge-demo
```

See [guardian/README.md](guardian/README.md).

## Guardian Authority Corpus v0.1

Governed reference layer for critical reasoning — scope, jurisdiction, version, and license-aware citation routing. Mock corpus only; no vector search, no cloud.

```bash
python guardian_authority/cli.py run-demo
python guardian_authority/cli.py evaluate-claim "A clean file is automatically safe for AI memory."
```

See [guardian_authority/README.md](guardian_authority/README.md).

## Evolution Prize Validation Workbench

Construction A+ on Natural Math — falsifiable computational bridge for Evolution 2.0 Initial Discovery (not chemical proof).

```bash
python evolution_prize_validation/cli.py run-all --seed 42
python evolution_prize_validation/cli.py build-submission-packet
```

See [evolution_prize_validation/README.md](evolution_prize_validation/README.md).

## Fractalish Field App PWA v0.1

Local-first offline training session recorder — converts phone session inputs into ReceptorEvent bundles. Private semi-sim field device; not public, not app-store.

```bash
python -m http.server 8010 --directory field_app/app

python field_app/tools/field_app_cli.py validate-sample
python field_app/tools/field_app_cli.py convert-sample-to-receptors
```

See [field_app/README.md](field_app/README.md).

## Operational Self + Fractal Attractor Memory v0.1

Routed continuity memory spine — light compression, attractor topology, scars, fog, replay routes. Operational self is continuity structure, not consciousness.

```bash
python operational_self/cli.py run-demo
python operational_self/cli.py retrieve "pressure is not truth"
python operational_self/cli.py replay-route "resume product build"
```

See [operational_self/README.md](operational_self/README.md).

## Cognitive Basin Workbench

Local experimental workbench that makes PERCEPT → ATAL → RIGOR → CIRCUIT → GUARD → SERA → SessionGlyph **visible and runnable**. A traceable, stateful, ternary-gated cognition simulator — **not consciousness**, not a chatbot.

```bash
python experiments/cognitive_basin_workbench/run_workbench.py
# dashboard: cd experiments/cognitive_basin_workbench/dashboard && python -m http.server 8001
```

See [experiments/cognitive_basin_workbench/README.md](experiments/cognitive_basin_workbench/README.md).

## Cognitive Basin Simulation v1

First visible moving-basin simulation with **FractalMemoryMap** retrieval topology over CIRCUIT. Not consciousness — stateful simulated continuity only.

```bash
python experiments/cognitive_basin_sim_v1/run_simulation.py
```

## Maze benchmark

Maze-running is a controlled benchmark for local decision-making, memory, revisits, traps, and constraint navigation. It is not a claim of general intelligence.

```bash
python experiments/grok_sandbox/benchmark/run_maze_benchmark.py
```

## Documentation

- [docs/architecture_note.md](docs/architecture_note.md)
- [docs/minimal_runtime_spec.md](docs/minimal_runtime_spec.md)
- [docs/cognitive_basin_core_note.md](docs/cognitive_basin_core_note.md)
- [docs/natural_math_v3_6_core_note.md](docs/natural_math_v3_6_core_note.md)
- [docs/fractalish_morphology_note.md](docs/fractalish_morphology_note.md)
- [docs/non_claims.md](docs/non_claims.md)
- [docs/test_plan.md](docs/test_plan.md)
- [LICENSE_PENDING.md](LICENSE_PENDING.md)

## Repository layout

```
fractalish-ai/
  fractalish_ai/       # Runtime package (Cognitive Basin + Natural Math + MCVA)
  examples/            # Runnable demos
  experiments/grok_sandbox/  # Maze benchmark (isolated)
  schemas/             # JSON schemas
  docs/                # Architecture and non-claims
  public/              # Static local demo page
  demo_outputs/        # Cognitive Basin demo JSON
  outputs/             # Generated outputs
```

Built from curated reference library at `C:\Users\moop\FractalishBuild\reference\fractalish_curated_reference_library`. v4 commit-candidate zip used as baseline implementation.