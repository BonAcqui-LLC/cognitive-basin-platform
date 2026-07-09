from __future__ import annotations

import math

import numpy as np


def origin_state() -> tuple[int, int, int]:
    return (0, 0, 0)


def neighbors_6(position: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    x, y, z = position
    return [
        (x + 1, y, z),
        (x - 1, y, z),
        (x, y + 1, z),
        (x, y - 1, z),
        (x, y, z + 1),
        (x, y, z - 1),
    ]


def quadrance(u: tuple[int, int, int] | np.ndarray, v: tuple[int, int, int] | np.ndarray) -> int:
    return int(sum((int(u[i]) - int(v[i])) ** 2 for i in range(3)))


def spread(u: tuple[int, int, int] | np.ndarray, v: tuple[int, int, int] | np.ndarray) -> float:
    q_u = quadrance(u, (0, 0, 0))
    q_v = quadrance(v, (0, 0, 0))
    if q_u == 0 or q_v == 0:
        return 0.0
    cross = np.cross(u, v)
    q_cross = quadrance(cross, (0, 0, 0))
    return q_cross / (q_u * q_v)


def perpendicular_vector(v: tuple[int, int, int] | np.ndarray) -> np.ndarray:
    vec = np.array(v, dtype=int)
    for i in range(3):
        if vec[i] != 0:
            w = np.zeros(3, dtype=int)
            w[(i + 1) % 3] = vec[i]
            w[(i + 2) % 3] = -vec[(i + 1) % 3]
            if quadrance(vec, w) > 0:
                return w
    return np.array([1, 0, 0], dtype=int)


def rational_sqrt_approx(x: float, max_iter: int = 50) -> float:
    if x < 0:
        return 0.0
    a, b = 1, 1
    for _ in range(max_iter):
        a_new = (a + x * b) // 2
        b_new = a
        a, b = a_new, b_new
        if b == 0:
            break
        if a * a == x * b * b:
            return a / b
    return math.sqrt(x)


def bifurcation_children(v0: tuple[int, int, int] | np.ndarray, s: float) -> tuple[np.ndarray, np.ndarray]:
    parent = np.array(v0, dtype=int)
    w = perpendicular_vector(parent)
    q_v0 = quadrance(parent, (0, 0, 0))
    q_w = quadrance(w, (0, 0, 0))
    if q_v0 == 0 or q_w == 0:
        return parent.copy(), parent.copy()
    k_sq = (s / (1 - s)) * (q_v0 / q_w)
    k = rational_sqrt_approx(k_sq)
    if k == 0:
        return parent.copy(), parent.copy()
    v1 = parent + int(round(k)) * w
    v2 = parent - int(round(k)) * w
    return v1, v2
