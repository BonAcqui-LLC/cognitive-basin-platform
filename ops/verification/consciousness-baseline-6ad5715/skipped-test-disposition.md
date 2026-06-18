# Skipped Test Disposition

- Baseline main: `6ad571592874e4906b44d339af8a34c3e5e7f903`
- File: `tests/test_connectors.py`
- Prior skipped assertion site: `tests/test_connectors.py:48`
- Observed baseline behavior: the test skipped when symlink creation was unavailable in the local environment, which masked the actual out-of-root resolution assertion path on Windows.
- Environment factor: Windows symlink creation can be unavailable without Developer Mode or elevated symlink privilege.
- Classification: `STALE_SKIP`
- Disposition: repaired and skip removed

Repair summary:

1. The test now attempts the real symlink path when available.
2. If symlink creation is unavailable, it falls back to a bounded `Path.resolve` monkeypatch for the synthetic linked path instead of skipping.
3. The regression assertion now exercises the intended uppercase out-of-root blocking path rather than depending on a missing-file side effect.

Observed proof:

- `python -m pytest tests/test_connectors.py -q --tb=short -rs`
- Result: `3 passed`
- Subsequent aggregate acceptance includes connector coverage without any skipped-test dependence.
