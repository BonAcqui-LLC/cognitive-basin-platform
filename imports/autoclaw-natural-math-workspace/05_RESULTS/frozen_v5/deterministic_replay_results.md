# Natural Math v5 — Deterministic Replay & Isolation Results

**Date:** 2026-06-23 16:46 UTC
**SHA256:** E5AB47D41B82F6AF573866BE637BF3B0054D96C7F45A613EC6CAE2124AD84C7B

## Summary

- **Seeds tested:** 50
- **Step counts:** 0, 1, 35, 140
- **Total configs:** 200 (50 x 4)
- **Local cases:** 10
- **All deterministic:** YES
- **Failures:** 0

## All Tests Passed

All 200 cluster configurations produced **identical results across repeated runs** with both implicit (`params=None`) and explicit parameter dictionaries.

### Part A: Cluster Deterministic Replay

- All 50 seeds x 4 step counts = 200 configurations -> **identical on replay**
- Parameter dictionaries remain **unchanged** after each call
- Node structures do **not share identity** across runs (fresh deep copies)
- RNG traces (TraceRng.draws) match exactly

### Part B: Local Deterministic Cases

- 10 local cases with node sets from 1-10 nodes -> **all identical on replay**
- Model state uses **integers only** (no floats)
- Invariants pass after every step
- No global mutable state leakage

### Part C: Isolation Tests

- `run_cluster(0)` vs `run_cluster(1)` -> **independent** (no shared state)
- `run_cluster(0, steps=10)` x 3 -> **identical** each time
- Filesystem location independence -> **confirmed**
- Dictionary insertion order independence -> **confirmed**
- Global mutable state leakage -> **none found**
