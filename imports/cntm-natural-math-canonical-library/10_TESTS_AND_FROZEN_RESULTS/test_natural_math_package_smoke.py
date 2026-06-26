from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from natural_math.simulator import NaturalMathSimulator


def test_natural_math_package_reaches_inactive_state() -> None:
    simulator = NaturalMathSimulator()
    history_active, history_energy, history_forests, froze = simulator.run(max_steps=10_000)
    validation = simulator.validate()
    snapshot = simulator.snapshot()

    assert froze is True
    assert simulator.state.step_count == 198
    assert history_active[-1] == 0
    assert history_forests[-1] == 0
    assert history_energy[-1] == 0.0
    assert simulator.state.initial_forest_count == 3
    assert validation["energy_non_increasing"] is True
    assert validation["unique_node_ids"] is True
    assert validation["valid_parent_order"] is True
    assert validation["no_parent_cycles"] is True
    assert validation["no_active_overlap"] is True
    assert validation["nonnegative_energy"] is True
    assert validation["inert_energy_zero"] is True
    assert validation["forest_counter_consistent"] is True
    assert len(simulator.state.event_log) == simulator.state.step_count
    assert "event_totals" in snapshot
    assert snapshot["event_totals"]["extend_decisions"] >= 0
    assert snapshot["event_totals"]["restrict_deaths"] >= 0


def test_natural_math_cli_exports(tmp_path: Path) -> None:
    out_dir = tmp_path / "nm_out"
    result = subprocess.run(
        [sys.executable, "tools/natural_math_run.py", "--profile", "smoke", "--out", str(out_dir)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Simulation froze (Eventuality Theorem) at step 198" in result.stdout
    assert (out_dir / "natural_math_summary.json").exists()
    assert (out_dir / "natural_math_history.csv").exists()
    assert (out_dir / "natural_math_events.csv").exists()

    summary = json.loads((out_dir / "natural_math_summary.json").read_text(encoding="utf-8"))
    assert summary["step_count"] == 198
    assert summary["initial_forest_count"] == 3
    assert summary["birth_events"] == 0
    assert "validation" in summary
    assert "event_log" in summary
    assert "event_totals" in summary
    assert summary["validation"]["no_parent_cycles"] is True
    assert summary["validation"]["valid_parent_order"] is True


def test_natural_math_growth_demo_exercises_extend() -> None:
    simulator = NaturalMathSimulator(params={"iota": 1, "eta_sq": 0.0, "P_bifurcate": 10.0})
    layout = [
        ((0, 0, 0), (1, 0, 0), 100.0, 0),
        ((3, 0, 0), (-1, 0, 0), 1000.0, 1),
    ]
    history_active, _, _, froze = simulator.run(max_steps=20, seed_layout=layout)
    snapshot = simulator.snapshot()
    totals = snapshot["event_totals"]

    assert froze is False
    assert history_active[-1] > 0
    assert totals["extend_decisions"] > 0
    assert totals["single_child_extensions"] > 0


def test_natural_math_bifurcation_demo_exercises_bifurcation() -> None:
    simulator = NaturalMathSimulator(params={"iota": 1, "eta_sq": 0.0, "P_bifurcate": 1.0})
    simulator.add_obstacle((1, 0, 0))
    layout = [
        ((0, 0, 0), (1, 0, 0), 600.0, 0),
        ((4, 0, 0), (-1, 0, 0), 1000.0, 1),
    ]
    history_active, _, history_forests, froze = simulator.run(max_steps=200, seed_layout=layout)
    totals = simulator.snapshot()["event_totals"]

    assert froze is True
    assert history_active[-1] == 0
    assert history_forests[-1] == 0
    assert totals["bifurcations"] > 0
    assert totals["extend_decisions"] > 0
