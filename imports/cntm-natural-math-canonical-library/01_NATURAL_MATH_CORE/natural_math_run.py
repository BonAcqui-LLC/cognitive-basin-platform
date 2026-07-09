from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from natural_math.export import export_event_csv, export_history_csv, export_state
from natural_math.presets import get_profile
from natural_math.simulator import NaturalMathSimulator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the canonical Natural Math simulator package.")
    parser.add_argument(
        "--profile",
        choices=["smoke", "growth-demo", "obstacle-growth", "bifurcation-demo"],
        default="bifurcation-demo",
        help="Named run profile. Use 'smoke' for the closed-system inactive-state baseline.",
    )
    parser.add_argument("--max-steps", type=int, default=10_000, help="Maximum timesteps to run.")
    parser.add_argument("--seed", type=int, default=7, help="Deterministic PRNG seed.")
    parser.add_argument("--initial-energy", type=float, default=400.0, help="Starting energy per seed.")
    parser.add_argument("--p-bifurcate", type=float, default=None, help="Override base bifurcation threshold.")
    parser.add_argument("--e-reproduce", type=float, default=None, help="Override minimum energy for reproduction.")
    parser.add_argument("--eta-reproduce", type=float, default=None, help="Override efficiency threshold for reproduction.")
    parser.add_argument("--sigma-mutate", type=float, default=None, help="Override mutation stddev for offspring P_bifurcate.")
    parser.add_argument("--external-input", type=float, default=None, help="Override per-step energy input for open-system experiments.")
    parser.add_argument("--obstacles", action="store_true", help="Add simple test walls to exercise pressure and branching.")
    parser.add_argument("--out", type=Path, default=None, help="Optional output directory for JSON/CSV exports.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    profile = get_profile(args.profile)
    profile_params = dict(profile["params"])
    profile_params["seed"] = args.seed
    if args.p_bifurcate is not None:
        profile_params["P_bifurcate"] = args.p_bifurcate
    if args.e_reproduce is not None:
        profile_params["E_reproduce"] = args.e_reproduce
    if args.eta_reproduce is not None:
        profile_params["eta_reproduce"] = args.eta_reproduce
    if args.sigma_mutate is not None:
        profile_params["sigma_mutate"] = args.sigma_mutate
    if args.external_input is not None:
        profile_params["external_input"] = args.external_input
    simulator = NaturalMathSimulator(
        params=profile_params
    )
    for obstacle in profile.get("manual_obstacles", []):
        simulator.add_obstacle(obstacle)
    seed_layout = [
        (pos, direction, args.initial_energy if energy == 400.0 else energy, forest_id)
        for pos, direction, energy, forest_id in profile["seed_layout"]
    ]
    history_active, _, history_forests, froze = simulator.run(
        max_steps=args.max_steps,
        seed_layout=seed_layout,
        add_test_obstacles=bool(profile["add_test_obstacles"]) or args.obstacles,
    )
    validation = simulator.validate()

    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        export_state(args.out / "natural_math_summary.json", simulator.snapshot())
        export_history_csv(args.out / "natural_math_history.csv", simulator)
        export_event_csv(args.out / "natural_math_events.csv", simulator)

    print(f"Profile: {args.profile}")
    print(f"Starting Simulation. Forests: {simulator.state.initial_forest_count}")
    if bool(profile["add_test_obstacles"]) or args.obstacles:
        print("Test obstacles enabled.")
    if froze:
        print(f"Simulation froze (Eventuality Theorem) at step {simulator.state.step_count}")
    else:
        print(f"Simulation hit max_steps={args.max_steps} with {history_active[-1]} active sites remaining")
    print()
    print("--- FINAL REPORT ---")
    print(f"Total Steps: {simulator.state.step_count}")
    print(f"Final Active Sites: {history_active[-1]}")
    print(f"Peak Forests: {max(history_forests)}")
    print(f"Initial Forests: {simulator.state.initial_forest_count}")
    print(f"Final Active Forests: {history_forests[-1]}")
    print(f"New Forests Created: {simulator.state.birth_events}")
    print(f"Energy non-increasing (closed-system check): {validation['energy_non_increasing']}")
    print(f"Unique node ids: {validation['unique_node_ids']}")
    print(f"Valid parent order: {validation['valid_parent_order']}")
    print(f"No parent cycles: {validation['no_parent_cycles']}")
    print(f"No active overlap: {validation['no_active_overlap']}")
    print(f"Nonnegative energy: {validation['nonnegative_energy']}")
    print(f"Inert energy zero: {validation['inert_energy_zero']}")
    print(f"Forest counter consistent: {validation['forest_counter_consistent']}")
    if simulator.state.event_log:
        totals = simulator.snapshot()["event_totals"]
        print(f"Total extend decisions: {totals.get('extend_decisions', 0)}")
        print(f"Total bifurcations: {totals.get('bifurcations', 0)}")
        print(f"Total single-child extensions: {totals.get('single_child_extensions', 0)}")
        print(f"Total conflict losses: {totals.get('conflict_losses', 0)}")
        print(f"Total restrict deaths: {totals.get('restrict_deaths', 0)}")
        print(f"Total reproduction births: {totals.get('reproduction_births', 0)}")
    if froze:
        print()
        print("Smoke test reached an inactive state in this run.")
    else:
        print()
        print("Run stopped at max_steps before inactivity; do not claim theorem verification from this run alone.")
    if args.out is not None:
        print()
        print(f"Exports written to: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
