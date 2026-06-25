# Stage 1 — Remaining Ambiguities

## 1. Bonded Node Exclusion from Contact (Section 11)

The donor excludes bonded nodes from the contact distance computation during decision making. The frozen spec Section 11 does not explicitly address whether bonded nodes should be excluded from contact detection. The current implementation follows donor behavior: bonded pairs are excluded from distance computation. All 40 oracles pass with this behavior.

**Status**: Unresolved. Clarification from spec author needed.

## 2. sample_two PPM Recording

The sample_two function uses non-ppm randrange calls (arbitrary ranges, not 0-1000000). The spec defines PPM tracing as recording only randrange(0, 1000000) calls. In cluster initialization, sample_two's randrange calls use range(0, len(population)) which is NOT a ppm range (population size is 30, range is 0-30).

The cluster donor's 435 bond draws ARE ppm draws (0-1000000) and ARE recorded. sample_two calls are NOT recorded as ppm draws.

**Status**: Resolved. Implementation matches donor behavior.

## 3. Cluster Initialization: 80000 Bond Threshold

The donor uses a hardcoded threshold of 80000/1000000 (8%) for random bond formation during cluster initialization. This value is not derived from any Section 5 parameter and is not mentioned in the frozen spec.

**Status**: Unresolved. The donor hardcodes this value. Whether this should be a spec parameter or implementation constant is unclear.

## 4. Cluster Energy Base (55000 vs E0)

The donor uses a base energy of 55000 (with +-5000 random offset) for cluster nodes, not E0 (1,600,000). The frozen spec Section 18 does not specify the initial energy value for cluster nodes.

**Status**: Unresolved. The donor's 55000 base may be a testing convenience. Clarification needed on whether E0 applies to cluster initialization.

## 5. passed Diagnostic Definition

The cluster passed diagnostic in the donor is: alive >= 24 AND components == 1 AND avg_energy >= low_energy_cutoff AND resource_reached AND success_distance_passed. Section 22 describes the passed diagnostic conceptually but the exact thresholds are implementation details.

**Status**: Resolved. Implementation matches donor. Oracle fixtures verify exact consistency.

## 6. Deferred Capabilities

- Trace instrumentation (Stage 2)
- Full Layer B conformance suite (post-Stage 1)
- Layer C donor differential tests (post-Stage 1)
- Layer D deterministic replay suite (post-Stage 1)

**Status**: Acknowledged. These do not block Stage 1 classification as COMPLETE WITH WARNINGS.
