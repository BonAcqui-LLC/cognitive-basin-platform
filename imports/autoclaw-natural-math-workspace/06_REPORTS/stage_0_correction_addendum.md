# Stage 0 Correction Addendum

Generated: 2026-06-23 T06:07 EDT
Status: CORRECTION to Stage 0 implementation recommendation

## Corrected Finding

The original Stage 0 report stated that `natural_math_integer_oracle_runner.py` was a "40/40 conformant v5 implementation." This was incorrect.

### What Was Wrong

The integer oracle runner passes 25/25 local run_step fixtures. It does **not** implement `run_cluster()` — the second required v5 entry point specified in Section 2A. The cluster benchmark has 15 separate fixtures with their own runner (`natural_math_cluster_oracle_runner.py`). Neither runner implements both entry points.

### Corrected Totals

| Runner | Entry Points | Fixtures | Sections |
|---|---|---|---|
| `natural_math_integer_oracle_runner.py` | `run_step()` | 25/25 (local core) | 2-17 |
| `natural_math_cluster_oracle_runner.py` | `initialize_cluster()`, `cluster_step()`, `run_cluster_summary()` | 15/15 (cluster) | 18-22 |
| **Neither implements both** | — | — | — |

### Fixture Passing ≠ Full-Spec Conformance

A fixture suite tests exact input-output pairs. It does not test:
- Whether all parameter constraints are validated
- Whether every runtime invariant is checked
- Whether `rng=None` behavior is correct at all branches
- Whether the runner handles all edge cases in the spec
- Whether the runner exposes the exact API signatures required by Section 2A

Fixtures are necessary but insufficient evidence of full conformance.

## Corrected Implementation Path: B+C Revised

**Use the local integer oracle runner as the tested `run_step` implementation donor.**
**Use the cluster oracle runner as the tested `run_cluster` implementation donor.**
**Extract both into a clean importable package.**
**Audit and complete any spec gaps not covered by fixtures.**

The revised approach:
1. Extract `run_step` from the integer oracle runner into `natural_math_v5/run_step.py`
2. Extract cluster initialization, stepping, and the `run_cluster_summary` function from the cluster oracle runner into `natural_math_v5/cluster.py`
3. Create a unified `run_cluster(seed, params=None, steps=140)` wrapper matching the exact Section 2A signature
4. Identify and close spec gaps (see gap audits)
5. Add implementation-conformance tests beyond fixture coverage
6. Never rewrite original fixtures or expected outputs

## Distinction Between Test Types

| Category | Definition | Source |
|---|---|---|
| **Frozen oracle fixtures** | Exact input-output pairs from spec. SHA256-locked. Never modified. | `02_VALIDATION_EVIDENCE/NATURAL_MATH_V5/ORACLE_FIXTURES/` |
| **Implementation-conformance tests** | New tests for spec rules not covered by frozen fixtures (e.g., parameter edge cases, validation completeness). Written against the new library. | Stage 1 deliverables |
| **Scale reproduction tests** | Validate scale gate behavior against existing CSV/JSON evidence. | `02_VALIDATION_EVIDENCE/NATURAL_MATH_V5/SCALE_GATE_*/` |
| **Future extension tests** | Tests for Stages 2+. Separate test files, separate directories. | Stages 2+ |

## Stage 1 Revised Scope

Stage 1 must now:
1. Integrate both donor runners into one package
2. Create `run_cluster(seed, params=None, steps=140)` with the spec-required signature
3. Implement spec gaps identified in the gap audits
4. Add implementation-conformance tests
5. Verify all 40 frozen fixtures still pass
6. Verify new conformance tests pass

The original 7 Stage 0 deliverables remain valid as background research. Only the implementation recommendation and execution plan are revised.
