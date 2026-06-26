"""v3.6 core oracle tests — pytest-discoverable."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish_ai.natural_math.v3_6_core import run_oracles


def _oracle(name: str) -> bool:
    return run_oracles()[name]


def test_oracle_1_single_seed() -> None:
    assert _oracle("oracle_1_single_seed")


def test_oracle_2_contact_equality() -> None:
    assert _oracle("oracle_2_contact_equality")


def test_oracle_3_contact_strict() -> None:
    assert _oracle("oracle_3_contact_strict")


def test_oracle_4_bifurcation() -> None:
    assert _oracle("oracle_4_bifurcation")


def test_oracle_5_zero_gradient_fallback() -> None:
    assert _oracle("oracle_5_zero_gradient_fallback")


def test_oracle_6_bifurcation_colocation() -> None:
    assert _oracle("oracle_6_bifurcation_colocation")


def test_oracle_7_pressure_update() -> None:
    assert _oracle("oracle_7_pressure_update")


def test_oracle_8_growth_initiation() -> None:
    assert _oracle("oracle_8_growth_initiation")


def main() -> int:
    results = run_oracles()
    failed = [name for name, ok in results.items() if not ok]
    print("Natural Math v3.6 Oracle Results")
    for name, ok in results.items():
        print(f"  {name}: {'PASS' if ok else 'FAIL'}")
    if failed:
        print(f"\nFailed: {', '.join(failed)}")
        return 1
    print("\nAll oracles passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())