# Guardian Authority Corpus v0.1

Guardian Authority Corpus is a **local-first governed reference layer** for critical AI reasoning. Authoritative material enters as structured, provenance-preserving, version-aware, license-aware, jurisdiction-aware evidence — not automatic truth.

## What it is

- Mock/sample authority corpus (dictionary, encyclopedia, government rules, standards, STEM)
- Transparent keyword citation routing (no embeddings, no vector search)
- Claim evaluation with scope, jurisdiction, version, and license checks
- Conflict detection (version, jurisdiction, scope, definition)
- AuthorityReceptorEvent bridge to ReceptorEvent → BasinLink → Cognitive Basin
- FractalMemoryMap authority snapshot with HOLD/fog regions

## What it is not

- Not a real dictionary, encyclopedia, or legal database
- Not RAG or vector retrieval
- Not automatic truth assignment
- Not a model API or cloud service
- Not production legal/compliance advice

## Why authoritative corpora should not become automatic truth

A dictionary entry defines words; it does not prove regulatory application. A government rule applies within jurisdiction. A standard applies at a version. Guardian Authority Corpus routes claims through governed citation paths so RIGOR and GUARD evaluate support within scope.

## Why scope, version, jurisdiction, and license matter

| Dimension | Hazard if ignored |
|-----------|-----------------|
| Scope | Lexical definition applied as regulation |
| Version | Superseded standard treated as current |
| Jurisdiction | Local rule treated as universal |
| License | Proprietary content used without permission |

## Local sample corpus

All samples under `samples/corpus/` are **invented mock records** marked `mock_only`. They demonstrate structure, not corpus ownership.

## Commands

```bash
python guardian_authority/cli.py run-demo
python guardian_authority/cli.py ingest guardian_authority/samples/corpus/mock_dictionary_entries.json
python guardian_authority/cli.py ingest guardian_authority/samples/corpus/mock_government_rules.json
python guardian_authority/cli.py evaluate-claim "A clean file is automatically safe for AI memory."
python guardian_authority/cli.py evaluate-claim "A source can be authoritative within one scope and irrelevant outside it."
python guardian_authority/cli.py detect-conflicts
python guardian_authority/cli.py export-dashboard
python guardian_authority/cli.py purge-demo
```

## Output files

| File | Contents |
|------|----------|
| `authority_sources.json` | Ingested sources |
| `authority_records.json` | All records |
| `authority_claims.json` | Evaluated claims |
| `citation_routes.json` | Citation route candidates |
| `conflicts.json` | Detected conflicts |
| `guard_decisions.json` | Authority + basin guard results |
| `receptor_events/` | ReceptorEvent JSON per evaluation |
| `fractal_memory_map_authority_snapshot.json` | FMM topology snapshot |
| `session_glyph_authority_update.json` | Continuity update |
| `dashboard_summary.json` | Dashboard bundle |
| `audit.jsonl` | Append-only audit |

## Dashboard preview

```bash
python guardian_authority/cli.py run-demo
cd guardian_authority/dashboard
python -m http.server 8006
```

## Cognitive Basin integration

AuthorityReceptorEvent converts to base `ReceptorEvent` with governed provenance. `receptor_event_to_decision_record()` runs PERCEPT → RIGOR → GUARD. Unsupported, contradicted, and out-of-scope claims route to HOLD or WATCH. Authority never auto-sets GUARD=PROCEED.

## Guardian Intake integration

Guardian Intake Gateway controls hostile intake. Guardian Authority Corpus controls authoritative intake. Both produce governed ReceptorEvents with lifecycle records, license status, retention policy, and purge demo. Mock corpus files are governed reference artifacts, not raw trusted knowledge.

## Non-claims

- No real legal, regulatory, or standards authority
- No production citation verification
- Heuristic routing only

## Deferred production features

- Live dictionary/encyclopedia APIs (with license)
- Enterprise policy connectors
- Verified legal databases
- ML-based claim extraction
- Vector retrieval (if ever used, must remain subordinate to RIGOR/GUARD)

## Doctrine

Authority is scoped evidence, not automatic truth. RAG is not reasoning. Retrieval is not closure. HOLD remains sacred. Operator sovereignty always.