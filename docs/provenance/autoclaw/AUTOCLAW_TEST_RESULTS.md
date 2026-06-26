# AUTOCLAW Test Results

| Category | Collected | Passed | Failed | Skipped | Errors | Duration | Command |
|---|---:|---:|---:|---:|---:|---:|---|
| Original local fixtures | 25 | 25 | 0 | 0 | 0 | n/a | `redirected original_oracle_runner.py` |
| Original cluster fixtures | 15 | 15 | 0 | 0 | 0 | n/a | `redirected original_oracle_runner.py` |
| Stage 1.1 conformance | 292 | 292 | 0 | 0 | 0 | 0.520s | `pytest layer_b_conformance` |
| Donor differential | 66 | 66 | 0 | 0 | 0 | n/a | `redirected compare_donors.py` |
| Deterministic replay | 210 | 210 | 0 | 0 | 0 | n/a | `redirected run_tests.py` |
| Trace equivalence | 5 | 5 | 0 | 0 | 0 | 0.070s | `pytest test_trace_equivalence.py` |
| Stage 2 extension harness | 107 | 107 | 0 | 0 | 0 | 0.460s | `pytest extension_harness` |
| Mode equivalence | 240 | 240 | 0 | 0 | 0 | n/a | `redirected _stage2_oracle_runner.py` |
| RNG equivalence | 6 | 6 | 0 | 0 | 0 | 0.070s | `pytest test_rng_equivalence.py` |
| Mutation resistance | 12 | 12 | 0 | 0 | 0 | 0.080s | `pytest test_mutation_resistance.py` |
| State isolation | 8 | 8 | 0 | 0 | 0 | 0.080s | `pytest test_state_isolation.py` |
| Proposal validation | 4 | 4 | 0 | 0 | 0 | 0.140s | `pytest -k proposal subset` |

## Stage 2 Performance

- Baseline: 0.024824s
- Harness no extensions: 0.338111s (1262.06%)
- Harness with noop: 0.347185s (1298.61%)
- Hash verification passed: True
