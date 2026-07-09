# Guardian Authority Corpus:
## A Governed Reference Layer for Critical AI Reasoning

**Version 0.1 — Local Prototype Doctrine**

---

## Thesis

Fractalish AI does not need to memorize every authority. It needs to **route claims through authority**.

Authoritative material is **scoped evidence**, not automatic truth.

---

## Core Principles

1. A dictionary entry is not truth by itself.
2. An encyclopedia entry is not truth by itself.
3. A government rule is not universal truth by itself.
4. A technical standard is not universal truth by itself.
5. A manual is not truth outside its scope/version.
6. A passed scan is not permission for memory.
7. A citation is not proof unless the citation route is valid.

---

## Required Metadata

Every authority record carries:

- **Provenance** — source, publisher, retrieval reference
- **Scope** — domain of applicability
- **Jurisdiction** — geographic/legal territory
- **Version** — effective date, supersession chain
- **License** — usage permissions
- **Confidence / uncertainty** — epistemic bounds

---

## Citation Routing

```
User Claim
  → Keyword/scope match (transparent, no embeddings)
  → CitationRoute candidates
  → Scope match check
  → Jurisdiction match check
  → Version match check
  → License allowed check
  → Conflict detection
  → Support status
  → GUARD recommendation
  → ReceptorEvent → BasinLink → RIGOR → GUARD
```

A **clean citation route** with matching scope, jurisdiction, and version may support a **scoped claim** (WATCH — not auto-PROCEED).

A **broken citation route** produces WATCH or HOLD.

---

## Conflict Classes

- Version conflict (superseded standards/rules)
- Jurisdiction conflict (same topic, different territories)
- Scope conflict (lexical vs regulatory)
- Definition conflict (ambiguous terms)
- Direct contradiction
- License conflict

---

## Integration with Guardian Intake

| Layer | Role |
|-------|------|
| Guardian Intake Gateway | Hostile/untrusted intake membrane |
| Guardian Authority Corpus | Governed authoritative reference intake |
| ReceptorEvent | Evidence bridge — not truth |
| RIGOR | Checks whether claims are supported within scope |
| GUARD | Decides PROCEED / WATCH / HOLD / REVERSE |
| SessionGlyph | Remembers unresolved HOLDs |

---

## Non-Claims

- Not a legal database
- Not production compliance
- Not RAG replacement for reasoning
- Mock corpus only in v0.1

---

## Closing

Retrieval alone is not reasoning. RAG alone does not prevent false closure. Authority must pass through RIGOR and GUARD. HOLD remains sacred. Operator sovereignty always.