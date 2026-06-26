# Technical Assessment: Natural Math “Stick” Mechanism

## Status

Melissa’s program is a valid executable agent-aggregation experiment after indentation restoration. It is not yet a crystal-physics model, and its present results do not isolate the proposed deficit-coupling mechanism from several easier causes of clustering.

This distinction does not make the work unimportant. The mechanism supplies a useful missing primitive for Natural Math: **formation**. Once nodes enter a bonded topology, that topology changes later movement, resource use, and reachable states. Form is no longer only an output; it becomes an active constraint on what happens next.

## What the v4 program actually implements

Each node has position, energy, age, life status, and a list of nearby “bonds.” Nodes move according to a normalized social direction plus a spring-derived direction. Nearby nodes are assigned links up to a maximum degree of three. Linked nodes equalize energy, move more slowly, consume less energy, and receive an optional energy increment.

For seed 42, the restored program completes 720 steps with all 20 nodes alive and final cluster sizes:

`[5, 4, 4, 3, 2, 2]`

That output is reproducible for the same random seed.

## Important implementation findings

### 1. Bonds are reconstructed, not persistent

`form_bonds()` clears every living node’s bond list on every step and rebuilds a proximity graph. A link therefore has no independent persistence or history. The apparent persistence comes from continued proximity, movement damping, spring steering from the previous step, and favorable metabolism.

A true “stick” mechanism needs bond hysteresis:

- form at `d <= d_form`;
- persist while `d <= d_break`;
- require `d_break > d_form`;
- break only by an explicit condition.

The hardened v5 implementation adds this.

### 2. The code and documents use different physical ranges

The explanatory documents describe a sensing distance of 25 and a bonding distance of 2. The supplied v4 code uses a sensing distance of 50 and a bonding distance of 4.

It also permits bond assignment out to distance 4 while skipping spring action beyond distance 3. These thresholds should not be treated as one validated parameter set.

### 3. The survival result is partly built into the metabolism

With the supplied values:

- base consumption = `0.5`;
- saving per bond = `0.6`;
- reward per bond = `0.1`.

One bond reduces consumption to zero and then adds energy. Any bonded node is therefore an energy-positive node until capped at `E0`. This explains why the seed-42 run finishes with every sampled node at the energy cap.

That is acceptable only if the reward represents an explicit environmental supply. It is not a closed finite-energy system otherwise. Hardened v5 defaults to zero external inflow and maintains a complete energy ledger.

### 4. Deficit attraction is not yet isolated

The proposed term is:

`deficit_strength * depletion_p * depletion_q`

Its maximum value in v4 is 20, while the raw energy difference between initially sampled nodes can be well above 100. The raw energy differential can therefore dominate the claimed shared-depletion attraction.

A preliminary multi-seed ablation also shows that removing the deficit term does not remove clustering in the supplied parameter regime. Initial proximity, energy-difference steering, repeated proximity-link reconstruction, spring steering, the boundary, and bond metabolism can produce similar aggregates.

The correct claim is therefore:

> The complete rule set generates clustered states under the tested software conditions.

It is not yet:

> Shared depletion has been shown to cause the clustered states.

That stronger causal statement requires preregistered ablations.

### 5. Distance weighting differs from the written equation

The technical document gives:

`g += (1 / Q) * effective_difference * displacement`

The code uses:

`g += (1 / sqrt(Q)) * effective_difference * displacement`

Because displacement magnitude is also `sqrt(Q)`, the code largely cancels distance from each neighbor’s contribution magnitude before normalization. The written rule makes nearer nodes more influential.

Hardened v5 implements the written `1/Q` form.

### 6. Spring stiffness does not operate as a true magnitude

v4 adds the spring vector to a unit social vector and normalizes the total. The final motion is then assigned an almost fixed speed. Normalization erases most force-magnitude information, so “spring stiffness = 0.5” primarily changes direction rather than producing a proportional displacement.

Hardened v5 keeps social velocity and spring displacement separate, adds them, and clamps only the final speed.

### 7. Energy equalization is order-dependent

v4 equalizes every accepted pair immediately while scanning pairs in node-ID order. For a node with multiple links, the result can depend on which pair is processed first. This conflicts with the stated snapshot/simultaneous-update rule.

Hardened v5 gathers new edges first, then performs order-independent, energy-conserving equalization on new-bond components.

### 8. “Crystal atom” is presently a metaphor

The model has no lattice symmetry, crystallographic orientation, interatomic potential, nucleation free energy, temperature, phase boundary, grain orientation, dislocation, or grain-boundary mechanics. It should be described as a domain-agnostic finite-resource aggregation model, or a crystal-inspired agent model, until those physical elements are added.

## Why the mechanism matters to Morphological Coding

The strongest contribution is not that tired things attract. It is this closed causal loop:

1. local state changes motion;
2. motion creates a topology;
3. topology changes later motion and metabolism;
4. the changed future preserves consequences of the earlier encounter.

That is a candidate **morphological memory** mechanism. The cluster graph is a durable state that constrains later transitions.

It becomes a candidate **morphological code** only after an experiment defines and validates:

- an input alphabet, such as controlled depletion or field regimes;
- a morphological alphabet, such as isolated, paired, chain, branched, ring, or compact-cluster states;
- a decoder outcome, such as later survival, transport, branch selection, or response to a probe;
- reproducible mappings on held-out seeds and initial conditions;
- better-than-null decoding;
- intervention evidence showing that changing morphology changes the decoded outcome.

The morphology is the carrier. The validated mapping is the code.

## Required software validation sequence

### A. Restore and freeze v4

The indentation-restored file should remain unchanged as the historical implementation. Hash it and preserve seed-42 output.

### B. Run causal ablations

At minimum, compare:

- complete v4;
- no deficit coupling;
- no energy-difference term;
- no spring;
- no bond saving;
- no bond reward;
- no bond mechanism;
- persistent bonds versus reconstructed proximity links;
- written distance weighting versus implemented distance weighting.

Use at least 50 seeds per condition before making a causal claim.

### C. Preregister metrics

Measure:

- time to first link;
- bonded fraction over time;
- component-size distribution;
- maximum component size;
- bond lifetime distribution;
- topology turnover;
- energy ledger;
- survivor fraction;
- path length and radius of gyration;
- degree distribution;
- sensitivity to node-ID permutation;
- sensitivity to initial density.

### D. Establish formation, not merely aggregation

Perturb mature clusters and compare their recovery with unbonded controls. A formation effect exists when prior topology predicts later recovery after controlling for current positions and energy.

### E. Establish coding separately

Train a decoder on graph and geometric features, freeze it, and test held-out runs. Compare it with null labels and with a decoder using only current average energy. The morphology must add predictive information beyond the underlying scalar state.

## Files in this package

- `melissa_crystal_grain_v4_clean.py`: indentation-restored v4; mechanics unchanged.
- `melissa_v4_seed42_output.txt`: frozen seed-42 console output.
- `natural_math_stick_v5_hardened.py`: auditable comparison implementation.
- `stick_v5_seed42_output.json`: hardened closed-resource seed-42 output.
- `validate_stick_models.py`: seed-sweep and ablation harness.
- `stick_validation_10_seed.json`: initial diagnostic results.

## Claim boundary

This package demonstrates software aggregation and persistent topology in an agent model. It does not demonstrate crystal formation, physical chemistry, universal cross-domain validity, a memory device, or morphological coding by itself. It provides a concrete primitive and a falsifiable route for testing those stronger propositions.
