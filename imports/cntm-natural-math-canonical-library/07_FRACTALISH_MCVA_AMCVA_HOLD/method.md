# Fractalish Commons Method

Fractalish Commons is not a simple fractal detector. It is an open morphology and geometry-signal workbench.

The working hypothesis is narrower than "everything is fractal." Many finite physical systems under constraint produce recurring morphology families because they solve similar routing, branching, filling, cracking, flowing, recovering, and boundary problems. Some of those families are fractal-like. Others are circular, spiral, wave-like, gridded, cellular, laminar, crystalline, or visibly mixed.

The Commons MVP therefore uses a transparent pipeline:

1. ingest a single image, image pair, or sequence;
2. segment visible structure;
3. skeletonize and vectorize what survives segmentation;
4. extract descriptors;
5. estimate morphology-family and geometry-family scores;
6. quantify AMCVA and competing/complementary geometry signals;
7. route to MCVA, HOLD, or AMCVA;
8. export the trace, metrics, and record.

The expected artifact bundle is:

- raw image copy and hash,
- `morphology_trace.svg`,
- `preview_overlay.png`,
- `metrics.csv`,
- `metrics.xlsx`,
- `mcva_record.json`,
- `diff_report.md` for sequences,
- `comparison_report.md` for paired comparisons.

This MVP prefers transparency over overclaim. Every claim must travel with its trace.
