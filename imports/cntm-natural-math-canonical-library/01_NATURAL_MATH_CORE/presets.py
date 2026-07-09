from __future__ import annotations


def default_params() -> dict[str, float | int]:
    return {
        "tau": 8.0,
        "iota": 2,
        "eta_sq": 1.0,
        "gamma": 1.0,
        "P_hibernate": 40,
        "P_bifurcate": 20,
        "P_erode": 50,
        "Delta_P_contact": 5,
        "Delta_P_conflict": 2,
        "eps_extend": 10,
        "eps_sense": 2,
        "eps_conserve": 1,
        "eps_split": 14,
        "eps_spawn": 7,
        "beta": 0.8,
        "s": 0.25,
        "s_min": 1 / 16,
        "s_max": 1 / 2,
        "R": 25,
        "delta": 2,
        "trail_deposit": 0.5,
        "trail_decay": 0.01,
        "E_reproduce": 50,
        "eps_reproduce": 10,
        "eta_reproduce": 0.1,
        "E_max_seed": 100,
        "sigma_mutate": 1.0,
        "seed": 7,
    }


def smoke_profile() -> dict[str, object]:
    return {
        "params": {},
        "seed_layout": [
            ((0, 0, 0), (0, 1, 0), 400.0, 0),
            ((10, 0, 0), (0, 1, 0), 400.0, 1),
            ((-10, 0, 0), (0, 1, 0), 400.0, 2),
        ],
        "add_test_obstacles": False,
    }


def growth_demo_profile() -> dict[str, object]:
    return {
        "params": {
            "iota": 1,
            "eta_sq": 0.0,
            "P_bifurcate": 10.0,
        },
        "seed_layout": [
            ((0, 0, 0), (1, 0, 0), 100.0, 0),
            ((3, 0, 0), (-1, 0, 0), 1000.0, 1),
        ],
        "add_test_obstacles": False,
    }


def obstacle_growth_profile() -> dict[str, object]:
    return {
        "params": {
            "iota": 1,
            "eta_sq": 0.0,
            "P_bifurcate": 5.0,
        },
        "seed_layout": [
            ((0, 0, 0), (1, 0, 0), 400.0, 0),
            ((3, 0, 0), (-1, 0, 0), 1000.0, 1),
        ],
        "add_test_obstacles": True,
    }


def bifurcation_demo_profile() -> dict[str, object]:
    return {
        "params": {
            "iota": 1,
            "eta_sq": 0.0,
            "P_bifurcate": 1.0,
        },
        "seed_layout": [
            ((0, 0, 0), (1, 0, 0), 600.0, 0),
            ((4, 0, 0), (-1, 0, 0), 1000.0, 1),
        ],
        "add_test_obstacles": False,
        "manual_obstacles": [(1, 0, 0)],
    }


def get_profile(name: str) -> dict[str, object]:
    profiles = {
        "smoke": smoke_profile,
        "growth-demo": growth_demo_profile,
        "obstacle-growth": obstacle_growth_profile,
        "bifurcation-demo": bifurcation_demo_profile,
    }
    if name not in profiles:
        raise ValueError(f"Unknown Natural Math profile: {name}")
    return profiles[name]()
