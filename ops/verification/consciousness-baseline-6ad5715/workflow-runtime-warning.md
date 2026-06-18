# Workflow Runtime Warning Disposition

- Baseline main: `6ad571592874e4906b44d339af8a34c3e5e7f903`
- Workflow: `.github/workflows/ci.yml`
- Observed warning class: GitHub Actions runtime deprecation / stale official action runtime warning
- Prior versions: `actions/checkout@v4`, `actions/setup-python@v5`
- Repaired versions: `actions/checkout@v7`, `actions/setup-python@v6`
- Disposition: repaired in-branch

Why this change was made:

1. The predictive tranche was instructed to clear the baseline runtime warning before continuing.
2. The workflow uses official GitHub actions and the repair is a direct version lift with no change to repository release posture.
3. The change preserves the existing non-deploying CI behavior while removing the stale runtime warning path.

Observed local verification after the repair:

- Targeted connector suite: passed
- Targeted predictive and integration suites: passed
- Aggregate acceptance: passed locally
