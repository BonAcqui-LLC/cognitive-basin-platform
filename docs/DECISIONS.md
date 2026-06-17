# DECISIONS.md
# Auditable record of decisions in this recovery — 2026-06-16

All decisions recorded here. Date + rationale + evidence link. Preserve James Clow (architect) and Melissa Clow (Natural Math) provenance.

## M0 (this session)
- **2026-06-16**: Fresh session declared. All prior Grok reports, completion claims, and "verified" backups treated as untrusted evidence. Full scope retained. (Bootstrap directive)
- **2026-06-16**: Recovery root created at C:\Users\moop\Cognitive-Basin-Recovery-2026-06-16 with strict subdirs. Git initialized. .gitignore written *before* ingesting any project source (prevents accidental credential or personal data inclusion).
- **2026-06-16**: Production Cloudflare (routes, DNS, KV data, secrets, Email Routing, custom domains) explicitly protected — read-only audit only. No mutations. Staging only on workers.dev if free and isolated.
- **2026-06-16**: Cost discipline: local-first, free tiers, existing subs (including ~5M Qwen tokens/mo). No R2 or paid activation without explicit price check + approval recorded here.
- **2026-06-16**: Canonical library location chosen per directive: C:\Users\moop\Cognitive-Basin-Canonical-Library (separate from platform repo). Will contain only curated, provenance-tagged evidence. Large binaries (FractalishBuild full tree) will not be copied wholesale.
- **2026-06-16**: TeamNarrative and author attribution: James Clow (lead synthesizer, architect), Melissa Clow (co-author, Natural Math, conceptual). Will be reflected in canon docs and code headers.
- **2026-06-16**: No "ceremonial reports". All updates via the 4 required docs + manifests + evidence. Compact. Evidence-linked.

## Later entries (none yet)
(Each future decision will note: what was chosen, why, alternatives considered, evidence, cost impact, scope impact, author note if relevant.)
