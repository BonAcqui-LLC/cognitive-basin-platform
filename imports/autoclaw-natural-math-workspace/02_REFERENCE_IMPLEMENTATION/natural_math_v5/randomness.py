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



def sample_two(rng: TraceRng, seq: list[Any]) -> tuple[Any, Any]:
    """Section 8: random unordered pair without replacement.

    Algorithm (per spec):
    1. randrange(0, len(seq)) to pick first index
    2. Remove that index from sequence (preserving order)
    3. randrange(0, len(remaining)) to pick second index
    4. Return (seq[idx1], remaining[idx2])

    Does NOT use rng.sample().
    """
    if len(seq) < 2:
        raise ValueError("sample_two requires at least 2 items")
    i = rng.randrange(0, len(seq))
    first = seq[i]
    remaining = seq[:i] + seq[i + 1:]
    j = rng.randrange(0, len(remaining))
    second = remaining[j]
    return first, second
