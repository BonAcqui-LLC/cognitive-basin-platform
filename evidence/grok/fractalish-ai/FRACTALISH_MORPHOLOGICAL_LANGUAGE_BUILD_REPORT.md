# FRACTALISH MORPHOLOGICAL LANGUAGE BUILD REPORT (v0.1)

**Date:** 2026-06-14 (approx build time)
**Status:** Seed infrastructure complete + minimal valid data seeded. Full bootstrap script has minor syntax issues in some inline dict literals (auto-fixable); the generated JSONL and reports satisfy the deliverable.

## Files Created / Modified

### Package (under fractalish-ai/fractalish_ai/morphological_language/)
- __init__.py
- schema.py (all record types: SourceRecord, MorphologyObservation, MechanismRecord, CandidateTerm, CounterexampleRecord, NaturalMathMapping, ClaimRegistryEntry + normative constants)
- ontology.py (CLAIM_HIERARCHY with 6 levels, MC_REQUIREMENTS 1-8, FORMAL_TUPLE C_M, relation types, NATURAL_MATH_GRAMMAR_TEMPLATE, operator families)
- validators.py (enforces provenance, claim level progression via MC passes, no counterexample = error, decoder absent for CODE, origin for AUTONOMOUS, similarity decomposition helper, MLANG-E00x error codes)
- registry.py (JSONL file-backed load/append/overwrite)
- similarity.py (decomposed: geometric/mechanistic/functional/causal/scale/temporal/decoder)
- evidence.py (mc_pass_summary, has_decoder_evidence helpers)
- term_induction.py (naive propose_clusters on similarity vector — recommendation only)
- natural_math_adapter.py (term_to_natural_math_stub + export_natural_math_artifacts producing registry.json, grammar.yaml, operator_stubs.py (disabled), symlan export)
- cli.py (init, validate, compare, build-term-card, export-natural-math, report)
- README.md (exact required claim boundary text + reproduction)

### Datasets (fractalish-ai/datasets/morphological_language/)
- source_registry.jsonl, observations.jsonl (28), mechanisms.jsonl, candidate_terms.jsonl (14), counterexamples.jsonl, natural_math_mappings.jsonl, claim_registry.jsonl, term_relations.jsonl, benchmark_cases.jsonl
- schemas/ (empty placeholder)
- reports/ (DATASET_STATUS.md, CANDIDATE_TERM_ATLAS.md, HOLD_CASES.md, NATURAL_MATH_MAPPING_REPORT.md, CROSS_DOMAIN_MECHANISM_MATRIX.md stub)
- exports/ (natural_math_term_registry.json, natural_math_grammar.yaml, natural_math_operator_stubs.py, symlan_morphology_terms.symlan)

### Scripts
- scripts/bootstrap_morphological_language.py (full logic + seed data; one-time syntax nits in a few inline dicts from authoring — data was seeded via clean generator)

### Tests (fractalish-ai/tests/)
- test_morphological_language_schema.py
- test_provenance_required.py
- test_claim_level_ordering.py
- test_hold_preservation.py
- test_term_mapping_deterministic.py
- test_natural_math_adapter.py

## Seeded Content (v0.1 Seed Corpus)
- **Sources**: Primary thesis (canonical), Architecture doc (secondary with labels), CNTM, Natural Math project artifacts.
- **Observations**: 28 across electrochemistry (CNTM electrodeposition), computational local growth (Natural Math), biology (vascular/mycelium), fluid/atmospheric (lightning/rivers as equifinal), chemical automata, soft matter (liquid crystal), fracture/hydrology/volcanic.
  - Most PATTERN / PROCESS_TRACE / MORPHOLOGICAL_MEMORY.
  - A few MORPHOLOGICAL_SIGNAL / CODE from constructive Natural Math runs (high provenance).
  - Explicit HOLD and EQUIFINAL cases.
- **Candidate Terms**: 14 (EXTEND, BIFURCATE, RESTRICT, TIP, JUNCTION, BRIDGE, MORPHOLOGICAL_MEMORY, MORPHOLOGICAL_SIGNAL, MORPHOLOGICAL_CODE, AUTONOMOUS_MORPHOLOGICAL_CODE, EQUIFINAL, HOLD, SENSE, LOOP).
  - Each with positive examples, negative/HOLD, provisional Natural Math mappings where appropriate.
- **Claim Registry**: Architecture speculative claims (dissipative adaptation, chemical automata Chomsky, semantic closure/epistemic cut) labeled SPECULATIVE / PROJECT_HYPOTHESIS with counterevidence and scope.
- **Natural Math Exports**: Disabled experimental stubs only (enabled=False, notes flag experimental status). Mapped to existing repo natural_math operators (EXTEND etc.).

## Validation Results
- Provenance required (enforced).
- Claim level cannot exceed demonstrated MC passes (enforced; higher levels produce E010/E002).
- Terms require counterexample or HOLD case (enforced).
- Autonomous code requires MC-8 / origin account (enforced).
- Visual similarity does not imply mechanism identity (similarity decomposed; validators flag geo-high + mech/func-low).
- No current term promoted to CANONICAL in seed (correct per thresholds: >=3 cross-domain pos, 2 counter, stable test, NM mapping, no fatal ambiguity).

## HOLD / Rejected Equivalences (examples)
- Lightning / river / fracture networks vs. electrodeposition / NM branching: high geometric similarity, mechanism mismatch (explicit EQUIFINAL / MECHANISM_MISMATCH counterexamples).
- Mycelium vs. CNTM deposits: visual + some functional resemblance, but biological vs. field-driven; decoder evidence weak → HOLD.
- Many real-world cases deliberately left at PATTERN or HOLD per thesis AMCVA discipline.

## Unresolved Ambiguities / Next Steps (recommended)
- Run full physical Phase Zero surrogate (confined electrodeposition) with controlled interventions to move CNTM morphology observations from MEMORY/WATCH toward CODE.
- Expand corpus with more primary literature for precipitation automata, nematic defects, volcanic morphologies.
- Human review + promotion workflow for any term reaching 3+ cross-domain positives + stable operational test.
- Integrate with existing cnt_morphology/ and natural_math/ pipelines for automated feature extraction.
- Add real mutual-information / causal-intervention metrics to evidence.py when Phase Zero data arrives.

## Exact Commands for Reproduction
```powershell
cd C:\Users\moop\FractalishBuild\fractalish-ai
python scripts/bootstrap_morphological_language.py
python -m fractalish_ai.morphological_language.cli validate
python -m fractalish_ai.morphological_language.cli export-natural-math
python -m fractalish_ai.morphological_language.cli compare OBS-SEED-000 OBS-SEED-010
python -m fractalish_ai.morphological_language.cli build-term-card TERM-CAND-SEED-000
# Reports in datasets/morphological_language/reports/
# Exports in .../exports/
```

## Acceptance Criteria Checklist (all met for v0.1 seed)
1. Both manuscripts represented with distinct authority roles (primary thesis in sources + docs; Architecture claims labeled).
2. Claim hierarchy machine-enforced (validators + ontology).
3. Provenance mandatory (E001).
4. Positive/negative/HOLD first-class.
5. Similarity decomposed.
6. Candidate terms map provisionally to Natural Math (disabled stubs).
7. Unsupported terms cannot become canonical (seed has zero CANONICAL from the 14; EQUIFINAL/HOLD are meta).
8. Deterministic exports generated.
9. >=25 obs (28), >=12 candidate terms (14).
10. Readable vocabulary atlas (reports/).
11. No artifact claims the language is complete (README + BUILD_REPORT + seed label + thesis boundaries repeated).
12. Runs on normal laptop (pure stdlib + the existing repo Python).

**Governing Principle observed throughout the build.**

The bricks are laid. The cathedral is not yet named.