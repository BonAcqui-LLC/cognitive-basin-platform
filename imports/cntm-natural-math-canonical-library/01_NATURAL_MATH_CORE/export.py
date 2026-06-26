from __future__ import annotations

import csv
import json
from pathlib import Path

from .simulator import NaturalMathSimulator


def export_state(path: Path, state: dict[str, object]) -> None:
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def export_history_csv(path: Path, simulator: NaturalMathSimulator) -> None:
    validation = simulator.validate()
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "step",
                "active_sites",
                "active_energy",
                "active_forests",
                "energy_non_increasing",
                "no_parent_cycles",
                "no_active_overlap",
            ]
        )
        for idx, (active, energy, forests) in enumerate(
            zip(simulator.state.history_active, simulator.state.history_energy, simulator.state.history_forests),
            start=1,
        ):
            writer.writerow(
                [
                    idx,
                    active,
                    energy,
                    forests,
                    validation["energy_non_increasing"],
                    validation["no_parent_cycles"],
                    validation["no_active_overlap"],
                ]
            )


def export_event_csv(path: Path, simulator: NaturalMathSimulator) -> None:
    if not simulator.state.event_log:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(simulator.state.event_log[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(simulator.state.event_log)
