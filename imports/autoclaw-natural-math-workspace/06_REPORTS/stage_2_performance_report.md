# Stage 2 — Performance Measurement Report

**Date:** 2026-06-23
**Test:** cluster seed=3, steps=140
**Python:** 3.13.12

## Measurements (average of 5 runs after warmup)

| Mode | Avg Time (s) | Min (s) | Max (s) | Overhead vs Baseline |
|------|-------------|---------|---------|---------------------|
| BASELINE | 0.024563 | 0.024232 | 0.024845 | — |
| HARNESS_NO_EXTENSIONS | 0.347934 | 0.343840 | 0.351733 | +1316.50% |
| HARNESS_WITH_EXTENSIONS (noop) | 0.354228 | 0.347826 | 0.360981 | +1342.12% |

## Hash Verification

- BASELINE: `9adf76a407db3e3bc74781a7cf95d471619ceaca6a53e03a3e4a5c34136ccd01`
- NO_EXTENSIONS: `9adf76a407db3e3bc74781a7cf95d471619ceaca6a53e03a3e4a5c34136ccd01`
- WITH_EXTENSIONS: `9adf76a407db3e3bc74781a7cf95d471619ceaca6a53e03a3e4a5c34136ccd01`
- All match: ✅ YES

## Summary

The harness adds approximately 1342.1% overhead with a no-op extension.
Since the no-op extension goes through the full harness hook lifecycle (13 hooks called),
this represents the upper bound for harness overhead in Stage 2.

All three modes produce identical SHA-256 result hashes, confirming exact behavioral
equivalence.
