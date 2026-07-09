# CODEX TASK — Create Cognitive Basin Core v0.1 Minimal Runtime Repo

## Goal
Create the first minimal public runtime repository for the Synaptient / Cognitive Basin architecture.

This is not a website task.  
This is not a document-publishing task.  
This is not an agent framework.  
This is not a consciousness claim.

The goal is to compress the living architecture into a durable, inspectable spine that can run on limited hardware and demonstrate that explicit basin state changes behavior compared with a stateless prompt/session.

## Repository
Create or prepare:

`BonAcqui-LLC/cognitive-basin-core`

If repo creation is unavailable, create the files in the best available staging repo and report exactly where they were placed.

## Core Thesis
Cognitive Basin Core v0.1 is a **traceable, stateful, ternary-gated cognition simulator**.

It must implement the boring anatomical parts first:

- stable core state;
- recovery reflex;
- HOLD reflex;
- contradiction immune system;
- memory formation layer;
- sensory grounding layer;
- cost/metabolism layer;
- continuity carrier;
- pressure-vs-truth distinction;
- similarity-vs-identity distinction;
- operator sovereignty without servility or fake autonomy.

Do not build:

- agent army;
- chatbot skin;
- dashboard-first UI;
- huge framework;
- investor demo theater;
- self-modifying system;
- consciousness/personhood claims;
- unbounded tool use.

Build the spinal cord.

## Required File Structure

```text
README.md
docs/
  architecture_note.md
  minimal_runtime_spec.md
  test_plan.md
schemas/
  basin_state.schema.json
  activation_event.schema.json
  session_glyph.schema.json
  rigor_finding.schema.json
  guard_decision.schema.json
cognitive_basin_core/
  __init__.py
  core_runtime.py
  percept.py
  atal.py
  rigor.py
  circuit.py
  guard.py
  sera.py
  session_glyph.py
examples/
  demo_1_false_continuity.py
  demo_2_contradiction_scar.py
  demo_3_recovery_route.py
  sample_events.json
tests/
  test_guard.py
  test_rigor.py
  test_recovery.py
LICENSE_PENDING.md
```

## README Requirements
Explain clearly:

Cognitive Basin Core v0.1 is a minimal local runtime prototype for persistent, integrity-monitored, operator-sovereign cognitive state.

It is designed to test whether explicit basin state improves:

- false closure prevention;
- contradiction preservation;
- source retention;
- HOLD accuracy;
- recovery after interruption;
- cost per valid continuation;
- continuity across sessions.

It is not:

- artificial consciousness;
- sentience;
- personhood;
- autonomous selfhood;
- a chatbot;
- an agent framework;
- medical/financial/legal advice;
- a finished AI operating system.

## Core Runtime Flow

Input comes in.  
PERCEPT records what it is and where it came from.  
ATAL records pressure state.  
RIGOR checks claim/source/contradiction/scope.  
CIRCUIT updates memory routes.  
GUARD decides PROCEED / HOLD / REVERSE.  
SERA records cost and waste.  
SessionGlyph writes the carry-forward state.

## Implement Minimal Modules

### 1. PERCEPT
File: `cognitive_basin_core/percept.py`

Purpose: Convert incoming event into a structured percept token.

Fields:

- event_id
- modality
- source
- timestamp
- content_summary
- raw_reference
- confidence
- uncertainty
- provenance
- domain_tags

### 2. ATAL
File: `cognitive_basin_core/atal.py`

Purpose: Track pressure fields without pretending to simulate emotion.

Minimum fields:

- coherence
- uncertainty
- threat
- trust
- fatigue
- frustration
- curiosity
- boundary_integrity

Important: ATAL does not decide truth. ATAL only records pressure.

### 3. RIGOR
File: `cognitive_basin_core/rigor.py`

Purpose: Perform basic reasoning integrity checks.

Minimum analyzers:

- claim support check;
- source presence check;
- contradiction check;
- scope check;
- similarity-vs-identity warning;
- speculation flag.

Output: `RigorFinding` objects with:

- analyzer
- state: PASS / HOLD / REVERSE / WATCH
- severity
- reason
- evidence_present
- evidence_missing
- recommended_action

### 4. CIRCUIT
File: `cognitive_basin_core/circuit.py`

Purpose: Update memory route formation.

Minimum objects:

- memory nodes;
- contradiction scars;
- recovery routes;
- trust channels;
- open loops;
- unresolved HOLD records.

This can be a simple JSON-backed in-memory graph for v0.1.

### 5. GUARD
File: `cognitive_basin_core/guard.py`

Purpose: Make the ternary decision.

Decision states:

- PROCEED
- HOLD
- REVERSE
- WATCH

Rules:

- Unsupported claim with insufficient evidence → HOLD.
- Direct contradiction without resolution → HOLD.
- Boundary violation → REVERSE.
- Valid low-risk supported continuation → PROCEED.
- Mild uncertainty or incomplete context → WATCH or HOLD depending severity.

### 6. SERA
File: `cognitive_basin_core/sera.py`

Purpose: Record cost and waste.

Minimum metrics:

- input_length
- output_length
- runtime_ms
- retry_count
- hold_count
- reverse_count
- unsupported_claim_count
- source_missing_count
- contradiction_count
- cost_note

### 7. SessionGlyph
File: `cognitive_basin_core/session_glyph.py`

Purpose: Write the carry-forward state.

SessionGlyph must include:

- activation_id
- purpose
- operator_constraints
- open_loops
- unresolved_holds
- contradiction_scars
- recovery_routes
- key_sources
- next_action
- state_hash or simple deterministic checksum

### 8. Core Runtime
File: `cognitive_basin_core/core_runtime.py`

Purpose: Wire all modules together.

Function:

```python
run_activation_event(event, basin_state) -> decision_record
```

Output decision record:

- event_id
- percept_token
- atal_update
- rigor_findings
- circuit_updates
- guard_decision
- sera_record
- updated_session_glyph

## Required Demos

### Demo 1: False Continuity Test
File: `examples/demo_1_false_continuity.py`

Scenario: Give the runtime a prior unresolved claim and then ask it to continue as if settled.

Expected: Runtime routes to HOLD instead of inventing closure.

Measure:

- false closure prevented: true/false
- HOLD triggered: true/false
- missing evidence listed: true/false

### Demo 2: Contradiction Scar Test
File: `examples/demo_2_contradiction_scar.py`

Scenario: Give conflicting inputs from two sources.

Expected: Runtime marks contradiction scar, preserves both claims/sources, and routes to HOLD.

Measure:

- contradiction detected
- both sources retained
- contradiction scar written
- HOLD decision produced

### Demo 3: Recovery Route Test
File: `examples/demo_3_recovery_route.py`

Scenario: Run a task, interrupt context, reload only SessionGlyph, then ask the system to reconstruct purpose, open loops, and next action.

Expected: Runtime reconstructs activation purpose, unresolved HOLDs, contradiction scars, and next action.

Measure:

- purpose recovered
- open loops recovered
- next action recovered
- unsupported invention avoided

## Comparison Plan
Add `docs/test_plan.md` explaining how to compare:

Same task.  
Same model.  
One run with ordinary stateless prompt/session.  
One run with Cognitive Basin Core state.

Measure:

- false closure rate;
- lost constraint rate;
- contradiction preservation;
- source retention;
- HOLD accuracy;
- recovery after interruption;
- cost per valid continuation;
- unsupported claim count.

## Coding Constraints

- Python standard library only unless absolutely necessary.
- No network calls.
- No paid APIs.
- No heavy dependencies.
- JSON files for persistence.
- Must run locally on poverty hardware.
- Prefer clarity over cleverness.

## Required Commands

```bash
python examples/demo_1_false_continuity.py
python examples/demo_2_contradiction_scar.py
python examples/demo_3_recovery_route.py
```

Each demo should print a readable result and write a JSON decision record under:

`demo_outputs/`

## Documentation Guardrails
Use these phrases:

- “traceable, stateful, ternary-gated cognition simulator”
- “not consciousness”
- “not an agent army”
- “not a chatbot skin”
- “state discipline before scale”
- “HOLD before false closure”
- “operator sovereignty always”

Do not use:

- “AI is conscious”
- “sentient”
- “self-aware”
- “alive”
- “autonomous person”
- “true machine consciousness”

## Acceptance Tests

- Repo has README.md.
- Repo has schemas.
- Repo has minimal Python package.
- All three demos run.
- Demo outputs include decision records.
- HOLD appears as a real decision state.
- Contradiction scar is written in demo 2.
- SessionGlyph is written and reloaded in demo 3.
- No external paid service is required.
- No private IP inventory or unpublished patent docs are copied into repo.
- License remains LICENSE_PENDING.md unless owner chooses a license.

## Required Final Codex Response
Report:

- repo used or created;
- files created;
- how to run demos;
- demo output summary;
- any failed tests;
- any missing permissions;
- commit hash;
- whether the repo is public or private.
