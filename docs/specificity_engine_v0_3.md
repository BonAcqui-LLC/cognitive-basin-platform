# Specificity Engine v0.3

## Status

Specificity Engine v0.3 is a deterministic local measurement and governance
component. It implements an executable interpretation of the Specificity
Thesis prototype while preserving the distinction between measurement,
epistemic truth, action governance, and Natural Math process state.

It does not establish that GSR, NGR, or Structural Debt Potential are
empirically valid across domains. Targets, comparison modes, weights,
resolution capacity, and debt thresholds require domain-specific validation.

## Measurement Contract

A `SpecificityTarget` declares only the features relevant to a stated purpose.
Each `TargetFeature` names:

- a path into the full developmental record;
- a path into the encoded or geometric form;
- a deterministic comparison mode;
- a positive target weight;
- an optional numeric tolerance.

The available comparison modes are:

- `EXACT`: canonical JSON equality;
- `NUMERIC`: normalized absolute error after tolerance;
- `SET`: Jaccard similarity;
- `SEQUENCE`: normalized longest-common-subsequence similarity.

For feature scores \(s_i \in [0,1]\) and positive target weights \(w_i\):

\[
\mathrm{GSR} =
\frac{\sum_i w_i s_i}{\sum_i w_i}
\qquad
\mathrm{NGR} = 1 - \mathrm{GSR}
\]

Missing target values score zero and remain explicit in the receipt. Fields
not selected by the target cannot change the result.

## Receipt Integrity

Measurement is performed once. The resulting immutable `MeasurementReceipt`
contains:

- algorithm version;
- representation and target identifiers;
- hashes of target-relevant reference and observed values;
- per-feature scores and weights;
- GSR and NGR;
- provenance references;
- a deterministic content-addressed receipt identifier.

Structural-debt assessment must consume the NGR already present in that
receipt. It cannot invoke measurement again.

## Structural Debt

`StructuralDebtInputs` carries non-negative values for discrepancy debt, scar
load, coercivity, remanence, branching burden, ambiguity load, SERA waste, and
applied NGR. `DebtPolicy` supplies explicit weights and capacity-relative
thresholds.

The specificity-local risk namespace is:

- `OPERATIONAL`
- `CAUTION`
- `CONSTRAINED`
- `CRITICAL`
- `EXCEEDED`

These are not Cognitive Basin action states.

## Namespace Boundaries

Cognitive Basin epistemic states remain:

- `SUPPORTED`
- `UNRESOLVED`
- `CONTRADICTED`

Cognitive Basin action states remain:

- `EXTEND`
- `HOLD`
- `RETRACT`

Natural Math local process states remain:

- `EXTEND`
- `SENSE`
- `RESTRICT`

The adapters preserve these namespaces. Specificity does not infer epistemic
truth. Debt pressure may constrain a requested Cognitive Basin action or
suggest a Natural Math process state through separate, explicit functions.
`HOLD` is not `SENSE`, and `RETRACT` is not `RESTRICT`.

## Persistence and Replay

`SpecificityLedger` appends JSONL events containing the measurement receipt,
debt assessment, and governed decision. Events are sequence-numbered and
hash-chained. Replay verifies:

- sequence continuity;
- the previous-event hash;
- each event hash;
- receipt arithmetic and content addressing;
- structural-debt arithmetic and policy classification;
- deterministic governance-adapter output;
- receipt references across assessment and decision.

Replay rejects modified, reordered, malformed, or internally inconsistent
events and reconstructs the final governed state when the chain is valid.

## Demonstration

Run:

```shell
python -m specificity_engine.demo --artifact-dir build/specificity-demo
python -m specificity_engine.acceptance --artifact-dir build/specificity-acceptance
```

The demonstration executes an exact training record, a degraded relocation,
and a repaired representation. It persists all three events and verifies that
replay reconstructs the final repaired `SUPPORTED / EXTEND` state.

## Provenance and Clean-Room Note

The user-supplied Qwen/Grok prototype artifacts were retained unchanged as
conceptual provenance. Current `main` also preserves the expanded prototype at
the repository root; v0.3 remains a separate implementation:

- compact `specificity_engine.py` SHA-256:
  `C1AE7D5D8BD22BBF0D4305F2817B827FCBD1E1511303142E37B99D39A38D2DB5`
- expanded prototype engine SHA-256:
  `A0DBFF1CE4F634F139C4EDE8DB1C1DD94DEBD8D6C518385BAAE1128BF243A8E7`
- Grok `specificity_engine_v0_2.py` SHA-256:
  `BBCEE3203DD2659E0DC1C057675B08F4DA7A3B8C1778084DA6385C0AA61B0BD8`
- prototype tar SHA-256:
  `B1F52A9F208CD31822EAAFB38DE7DE744719E8569FBEABB27B9234CF9CCC4E15`

Version 0.3 is a new standard-library implementation. It does not copy the
prototype implementation and removes its random scoring, implicit feature
counts, unused geometric form, and conflated governance enum.
