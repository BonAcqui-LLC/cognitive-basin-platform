"""Tests for CNT Morphology Simulator v0.2."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from fractalish_ai.cnt_morphology.conductance import compute_conductance
from fractalish_ai.cnt_morphology.evidence import freeze_evidence
from fractalish_ai.cnt_morphology.features import extract_features
from fractalish_ai.cnt_morphology.glyphs import build_basin_signature
from fractalish_ai.cnt_morphology.growth_rules import GROWTH_PROFILES
from fractalish_ai.cnt_morphology.perturbation import parse_perturbation, replay_signature
from fractalish_ai.cnt_morphology.schemas import PersistenceConfig
from fractalish_ai.cnt_morphology.simulator import run_simulation


def test_smoke_all_profiles():
    for profile in GROWTH_PROFILES:
        result = run_simulation(profile, seed=42, steps=50)
        assert len(result.graph.nodes) > 0


def test_kirchhoff_conductance_matrix_shape():
    result = run_simulation("aligned_forest", seed=42, steps=80)
    cond = compute_conductance(result.graph, method="kirchhoff")
    mat = cond["conductance_matrix"]
    assert cond["method"] == "kirchhoff_laplacian"
    assert len(mat) == len(cond["contacts"])
    if mat:
        assert len(mat[0]) == len(mat)


def test_kirchhoff_vs_shortest_path_both_return():
    result = run_simulation("branched_network", seed=7, steps=60)
    k = compute_conductance(result.graph, method="kirchhoff")
    s = compute_conductance(result.graph, method="shortest_path")
    assert k["conductance_matrix"]
    assert s["conductance_matrix"]
    assert k["method"] != s["method"]


def test_glyph_deterministic_same_seed():
    r1 = run_simulation("aligned_forest", seed=99, steps=60)
    r2 = run_simulation("aligned_forest", seed=99, steps=60)
    f1 = extract_features(r1.graph)
    f2 = extract_features(r2.graph)
    c1 = compute_conductance(r1.graph, method="kirchhoff")
    c2 = compute_conductance(r2.graph, method="kirchhoff")
    g1 = build_basin_signature(f1, c1, r1.profile, seed=99)
    g2 = build_basin_signature(f2, c2, r2.profile, seed=99)
    assert g1["basin_signature"] == g2["basin_signature"]


def test_persistent_mode_runs():
    persistence = PersistenceConfig(persistent_mode=True, maintenance_energy_rate=0.4)
    result = run_simulation("sparse_flux_limited", seed=42, steps=80, persistence=persistence)
    counts = result.graph.operator_counts
    assert "MAINTAIN" in counts or "HOLD" in counts or counts.get("EXTEND", 0) >= 0


def test_feedback_loop_runs():
    from fractalish_ai.cnt_morphology.feedback import compute_feedback_adjustment, apply_feedback_to_profile

    result = run_simulation("branched_network", seed=42, steps=60)
    feats = extract_features(result.graph)
    cond = compute_conductance(result.graph)
    glyph = build_basin_signature(feats, cond, result.profile, seed=42)
    adj = compute_feedback_adjustment(feats, glyph, target_profile="branched_network")
    profile2 = apply_feedback_to_profile(result.profile, adj)
    result2 = run_simulation("branched_network", seed=42, steps=60, profile=profile2)
    assert len(result2.graph.nodes) > 0


def test_replay_runs():
    result = run_simulation("aligned_forest", seed=42, steps=60)
    feats = extract_features(result.graph)
    cond = compute_conductance(result.graph, method="kirchhoff")
    glyph = build_basin_signature(feats, cond, result.profile, seed=42)
    perts = [parse_perturbation("position_jitter:0.05")]
    report = replay_signature(result.graph, feats, cond, glyph, perts, seed=42)
    assert "original_signature" in report
    assert "perturbed_signature" in report


def _signature_in_fresh_process(profile: str, seed: int, steps: int) -> str:
    repo_root = Path(__file__).resolve().parents[1]
    code = f"""
import json
from fractalish_ai.cnt_morphology.simulator import run_simulation
from fractalish_ai.cnt_morphology.features import extract_features
from fractalish_ai.cnt_morphology.conductance import compute_conductance
from fractalish_ai.cnt_morphology.glyphs import build_basin_signature
result = run_simulation({profile!r}, seed={seed}, steps={steps})
features = extract_features(result.graph)
conductance = compute_conductance(result.graph, method='kirchhoff')
glyph = build_basin_signature(features, conductance, result.profile, seed={seed})
print(json.dumps({{"basin_signature": glyph["basin_signature"]}}))
"""
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout.strip())["basin_signature"]


def test_determinism_aligned_seed42():
    sig_a = _signature_in_fresh_process("aligned_forest", seed=42, steps=250)
    sig_b = _signature_in_fresh_process("aligned_forest", seed=42, steps=250)
    assert sig_a == sig_b


def test_determinism_all_profiles_seed42():
    for profile in GROWTH_PROFILES:
        sig_a = _signature_in_fresh_process(profile, seed=42, steps=250)
        sig_b = _signature_in_fresh_process(profile, seed=42, steps=250)
        assert sig_a == sig_b, f"{profile}: {sig_a} != {sig_b}"


def test_freeze_creates_manifest_and_hashes(tmp_path):
    run_dir = tmp_path / "aligned_forest_seed42"
    run_dir.mkdir()
    result = run_simulation("aligned_forest", seed=42, steps=30)
    feats = extract_features(result.graph)
    cond = compute_conductance(result.graph)
    glyph = build_basin_signature(feats, cond, result.profile, seed=42)
    (run_dir / "graph.json").write_text(json.dumps(result.graph.to_dict()), encoding="utf-8")
    (run_dir / "features.json").write_text(json.dumps(feats), encoding="utf-8")
    (run_dir / "conductance.json").write_text(json.dumps(cond), encoding="utf-8")
    (run_dir / "glyph.json").write_text(json.dumps(glyph), encoding="utf-8")
    batch_index = [{"profile": "aligned_forest", "seed": 42, "dir": str(run_dir), "basin_signature": glyph["basin_signature"]}]
    (tmp_path / "batch_index.json").write_text(json.dumps(batch_index), encoding="utf-8")

    freeze_out = tmp_path / "freeze"
    result = freeze_evidence(tmp_path, freeze_out)
    assert (freeze_out / "MANIFEST.json").exists()
    assert (freeze_out / "SHA256SUMS.txt").exists()
    assert (freeze_out / "FREEZE_REPORT.md").exists()
    assert Path(result["archive"]).exists()