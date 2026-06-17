"""
Natural Math BasinLab workload tests.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.basinlab.contracts import ActionProposal
from python.basinlab.natural_math import (
    LocalProcessState,
    add_seed,
    advance_steps,
    attempt_spawn,
    calculate_energy,
    compare_growth_runs,
    create_growth_world,
    detect_contact,
    extract_growth_graph,
    inspect_frontier,
    inspect_node,
    restore_growth_world,
    seeded_three_world,
    snapshot_growth_world,
)
from python.basinlab.session import BasinLabSession


def test_seeded_three_world_has_three_starting_seeds():
    world = seeded_three_world(seed=11)
    assert len(world.nodes) == 3


def test_add_seed_and_inspect_node():
    world = create_growth_world(seed=1)
    node_id = add_seed(world, 3, 3, energy=140.0)
    node = inspect_node(world, node_id)
    assert node["position"] == (3, 3)
    assert node["energy"] == 140.0


def test_advance_steps_updates_frontier_and_energy():
    world = seeded_three_world(seed=13)
    before = calculate_energy(world)
    result = advance_steps(world, steps=3)
    assert result["step_count"] == 3
    assert calculate_energy(world) > before
    assert inspect_frontier(world)


def test_detect_contact_and_restrict_state_when_blocked():
    world = create_growth_world(seed=2, width=3, height=3)
    center = add_seed(world, 1, 1, energy=140.0)
    add_seed(world, 0, 1)
    add_seed(world, 2, 1)
    add_seed(world, 1, 0)
    add_seed(world, 1, 2)
    assert detect_contact(world, center) is True
    advance_steps(world, steps=1)
    assert world.nodes[center].state == LocalProcessState.RESTRICT


def test_attempt_spawn_respects_threshold_and_probability():
    world = create_growth_world(seed=3)
    node_id = add_seed(world, 10, 10, energy=150.0)
    world.spawn_probability = 1.0
    assert attempt_spawn(world, node_id) is True
    assert len(world.nodes) == 2


def test_snapshot_and_restore_preserve_world():
    world = seeded_three_world(seed=5)
    advance_steps(world, steps=2)
    snapshot = snapshot_growth_world(world)
    restored = restore_growth_world(snapshot)
    assert extract_growth_graph(restored) == extract_growth_graph(world)


def test_compare_growth_runs_reports_deltas():
    world_a = seeded_three_world(seed=7)
    world_b = seeded_three_world(seed=7)
    advance_steps(world_a, steps=2)
    advance_steps(world_b, steps=1)
    comparison = compare_growth_runs(world_a, world_b)
    assert comparison["step_delta"] == 1


def test_fixed_seed_replay_is_deterministic():
    world_a = seeded_three_world(seed=17)
    world_b = seeded_three_world(seed=17)
    advance_steps(world_a, steps=5)
    advance_steps(world_b, steps=5)
    assert extract_growth_graph(world_a) == extract_growth_graph(world_b)


def test_world_persists_inside_basinlab_session():
    with BasinLabSession() as session:
        session.load_bindings(
            {
                "seeded_three_world": seeded_three_world,
                "advance_steps": advance_steps,
                "extract_growth_graph": extract_growth_graph,
            }
        )
        create = session.execute_action(
            ActionProposal(
                "world-create",
                "Create seeded world",
                "world = seeded_three_world(seed=19)",
            )
        )
        advance = session.execute_action(
            ActionProposal(
                "world-advance",
                "Advance the retained world",
                "summary = advance_steps(world, steps=2)\ngraph = extract_growth_graph(world)",
                parent_event_id=create.event_id,
            )
        )
        namespace = session.materialize_namespace()
        assert create.basin.action.value == "EXTEND"
        assert advance.basin.action.value == "EXTEND"
        assert namespace["world"].step_count == 2
        assert namespace["summary"]["step_count"] == 2
        assert namespace["graph"]["step_count"] == 2


def test_world_tools_are_pickle_safe_for_session_use():
    world = seeded_three_world(seed=23)
    snapshot = snapshot_growth_world(world)
    restored = restore_growth_world(snapshot)
    assert calculate_energy(restored) == calculate_energy(world)
