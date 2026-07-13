# cognitive-basin-platform

Canonical **executable** platform for Fractalish / Cognitive Basin, EphUX, Guardian, Natural Math, BasinLab, Synaptient-related labs, simulations, clients, tests, and deployment infrastructure.

**Public research home (claims, visitor path, documents):** [https://fractalish.com](https://fractalish.com)  
**Site / docs repository:** [BonAcqui-LLC/fractalish](https://github.com/BonAcqui-LLC/fractalish)

Original architecture and research by **James Clow** and **Melissa Clow**, BonAcqui LLC.

---

## What this repository is

This is the **code and labs** repo. It is not the public claim surface.

| Concern | Where it lives |
|--------|----------------|
| Canonical public claims, claim boundary, visitor onboarding | [fractalish.com](https://fractalish.com) / [BonAcqui-LLC/fractalish](https://github.com/BonAcqui-LLC/fractalish) |
| Runnable labs, engines, tests, deployment scaffolding | **This repo** |

**Core rule (shared with the public site):** every claim must travel with its trace.

---

## July 2026 status (post-correction)

As of **July 2026**, after the adversarial audit and correction of the Resonant Morphology prototype notes:

- **Natural Math Leaf Generator** and **inverse test** are the active experimental pivot for local-growth morphology work.
- **Specificity Engine v0.3** prototype materials live under `specificity_thesis_prototype/` (draft implementation — not a finished product claim).
- **BasinLab**, Cognitive Basin package layout, connectors, evaluation, and related labs continue under their respective directories.
- Public claim language and the July 13, 2026 correction notice live on the site; do **not** treat root thesis files or internal notes in this repo as the public claim surface.

### Claim boundary (observe strictly)

When discussing or shipping demos, keep these bounds (aligned with the public site):

- Forward morphology readout is **lossy** (not bidirectional physical recovery).
- Prefer **parameterized local-growth boundary condition** language over uncorrected “resonance” prototype claims.
- Threshold form used in the corrected note: **θ_b = 2.8(T) + 1.5** (not the inverted draft form).
- A **Specificity Receipt** measures **target compliance** under a declared contract/comparator — **not** absolute truth.
- **Seed 42** (or any single seed) is **one deterministic trace**, not proof of robust morphology classes across seeds/species.
- Pivot for generative morphology testing: **Natural Math Leaf Generator** + inverse test (see site Natural Math page and archived correction note).

Do not upgrade these into product claims of sentience, universal decoding, or unrestricted physical resonance.

---

## Quick Start

### Requirements

- **Python 3.12+**
- Git

### Setup

```bash
git clone https://github.com/BonAcqui-LLC/cognitive-basin-platform.git
cd cognitive-basin-platform

# editable install + test tools
python -m pip install -e ".[dev]"
```

### Run tests

```bash
# full suite (may take a while; some suites skip optional environments)
python -m pytest tests/ -q

# focused examples
python -m pytest tests/test_basinlab_natural_math.py -q
python -m pytest tests/test_basinlab_package_layout.py -q
```

### Explore labs

| Path | Role |
|------|------|
| `natural_math_lab/` | Natural Math / acceptance-related lab code |
| `specificity_thesis_prototype/` | Specificity Engine v0.3 draft (`specificity_engine.py`, README) |
| `python/basinlab/` | BasinLab package surface |
| `cognitive_basin/` | Cognitive Basin package layout |
| `tests/` | Automated tests |
| `docs/` | Operational and design docs |
| `ops/` | Manifests, capability registry, ops tooling |
| `apps/`, `packages/`, `imports/` | App shells, packages, and governed imports |

Example (from repo root, after install):

```bash
# Inspect prototype package layout / docs
dir specificity_thesis_prototype
type specificity_thesis_prototype\README.md   # Windows
# cat specificity_thesis_prototype/README.md  # Unix
```

Runnable Leaf Generator demos may land under `natural_math_lab/` and `examples/` as they stabilize; prefer tests and lab READMEs for the current entry points.

---

## Architecture (high level)

```
cognitive-basin-platform/
├── natural_math_lab/              # Natural Math labs / acceptance
├── specificity_thesis_prototype/  # Specificity Engine v0.3 draft
├── python/basinlab/               # BasinLab implementation
├── cognitive_basin/               # Cognitive Basin package
├── evaluation_lab/                # Evaluation surfaces
├── memory_governance/             # Memory governance
├── connector_lab/ / provider_lab/ # Connectors / providers
├── ephux_local/                   # Local EphUX surfaces
├── apps/ packages/ imports/       # Applications and imports
├── tests/                         # pytest suite
├── docs/                          # Documentation
└── ops/                           # Ops manifests and tooling
```

**Relationship to the site repo**

- **fractalish** = public HTML research home, claim pages, documents, sitemap, Cloudflare Pages deploy.
- **cognitive-basin-platform** = executable platform, tests, labs, and internal structure for implementing and verifying the program under the public claim boundary.

---

## Reproducibility

- Prefer **tests** and **versioned lab scripts** over ad-hoc notebooks when making claims.
- Attach **seed, inputs, comparator, and receipt** (or equivalent trace) when reporting results.
- Public scientific wording should match [fractalish.com](https://fractalish.com) pages (Start Here, Natural Math, Specificity Thesis, Ageometrics), not stale root white-paper filenames in this tree.

---

## Contributing

1. Read [https://fractalish.com/start-here.html](https://fractalish.com/start-here.html) and the claim boundary on the homepage.
2. Open issues/PRs against this repository for **code and labs**.
3. Keep claim upgrades out of code comments and READMEs unless the site claim surface is updated first.
4. Run relevant pytest modules before opening a PR.

For public document contribution and review culture, see the site Contribute / Review pages.

---

## Links

| Resource | URL |
|----------|-----|
| Public site | https://fractalish.com |
| Start Here | https://fractalish.com/start-here.html |
| Natural Math | https://fractalish.com/natural-math.html |
| Specificity Thesis | https://fractalish.com/specificity-thesis.html |
| Ageometrics | https://fractalish.com/ageometrics/ |
| Documents | https://fractalish.com/documents.html |
| Site repo | https://github.com/BonAcqui-LLC/fractalish |
| This repo | https://github.com/BonAcqui-LLC/cognitive-basin-platform |

---

## License / IP

© BonAcqui LLC. See repository and company materials for licensing and IP terms. Research attribution: James Clow & Melissa Clow.

---

*README added per live audit 2026-07-13 (public-sharing readiness). Does not alter scientific claim content on fractalish.com.*
