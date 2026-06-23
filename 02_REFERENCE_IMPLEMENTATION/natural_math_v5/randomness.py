"""Natural Math v5 reference implementation — traceable RNG.

Frozen spec: Section 8 (Randomness)
"""

from __future__ import annotations

import random
from typing import Any


class TraceRng:
    """Section 8: Python-compatible random generator with PPM draw tracing.

    PPM draws (randrange(0, 1000000)) are traced to self.draws.
    Non-PPM draws (randint, choice, sample) are NOT traced.
    """

    def __init__(self, seed: int) -> None:
        self.inner = random.Random(seed)
        self.draws: list[int] = []

    def randrange(self, a: int, b: int) -> int:
        value = self.inner.randrange(a, b)
        if a == 0 and b == 1000000:
            self.draws.append(value)
        return value

    def randint(self, a: int, b: int) -> int:
        return self.inner.randint(a, b)

    def choice(self, seq: list[Any]) -> Any:
        return self.inner.choice(seq)

    def sample(self, population: list[Any], k: int) -> list[Any]:
        return self.inner.sample(population, k)


def sample_two(rng: TraceRng, items: list[Any]) -> tuple[Any, Any]:
    """Section 8: random unordered pair without replacement."""
    result = rng.sample(items, 2)
    return result[0], result[1]
