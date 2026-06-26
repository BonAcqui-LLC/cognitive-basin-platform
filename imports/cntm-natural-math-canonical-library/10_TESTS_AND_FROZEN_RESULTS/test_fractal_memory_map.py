"""FractalMemoryMap contract tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish_ai.fractal_memory_map import FractalMemoryLink, FractalMemoryMap, FractalMemoryNode


def test_fractal_memory_map_adds_node() -> None:
    fmm = FractalMemoryMap()
    node = FractalMemoryNode(node_id="n1", label="test node", salience=0.7)
    fmm.add_node(node)
    assert "n1" in fmm.nodes
    assert fmm.to_dict()["nodes"]["n1"]["label"] == "test node"


def test_fractal_memory_map_adds_contradiction_link() -> None:
    fmm = FractalMemoryMap()
    fmm.add_node(FractalMemoryNode(node_id="a", label="claim A", source="src_a"))
    fmm.add_node(FractalMemoryNode(node_id="b", label="claim B", source="src_b"))
    link = fmm.add_contradiction_link("a", "b", notes="conflict preserved")
    assert link.relation_type == "contradiction"
    assert fmm.nodes["a"].contradiction_score > 0
    assert fmm.nodes["b"].contradiction_score > 0
    assert len(fmm.links) == 1
    restored = FractalMemoryMap.from_dict(fmm.to_dict())
    assert len(restored.links) == 1
    assert restored.nodes["a"].contradiction_score > 0


def test_hold_region_not_returned_as_clean_attractor() -> None:
    fmm = FractalMemoryMap()
    fmm.add_node(FractalMemoryNode(node_id="clean", label="clean", salience=0.6, replay_score=0.3))
    fmm.add_node(FractalMemoryNode(node_id="fog", label="fog", salience=0.9, replay_score=0.9))
    fmm.mark_hold_region("fog")
    attractors = fmm.nearest_active_attractors()
    ids = [a["node_id"] for a in attractors]
    assert "clean" in ids
    assert "fog" not in ids


def test_replay_validated_route_ranks_above_unvalidated_route() -> None:
    fmm = FractalMemoryMap()
    fmm.add_node(
        FractalMemoryNode(
            node_id="validated",
            label="replay validated",
            salience=0.5,
            replay_score=0.8,
            current_distance_from_center=0.5,
        )
    )
    fmm.add_node(
        FractalMemoryNode(
            node_id="unvalidated",
            label="unvalidated",
            salience=0.5,
            replay_score=0.1,
            current_distance_from_center=0.5,
        )
    )
    fmm.add_recovery_route("validated", "validated", replay_validated=True)
    ranked = fmm.nearest_active_attractors()
    assert ranked[0]["node_id"] == "validated"
    assert ranked[0]["attractor_score"] > ranked[1]["attractor_score"]