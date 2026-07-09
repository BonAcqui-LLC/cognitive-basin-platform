# Guardian/HOLD Benchmark Results

## Aggregate

| Mode | Success | Success rate | Avg steps | HOLD overrides | Collisions |
|------|---------|--------------|-----------|----------------|------------|
| Without guardian | 1/6 | 0.1667 | 251.17 | 0 | 1478 |
| With guardian | 1/6 | 0.1667 | 251.17 | 1478 | 0 |

## Per maze

| Maze | Vanilla success | Guardian success | Δ holds | Δ collisions |
|------|-----------------|------------------|---------|----------------|
| simple | True | True | 0 | 0 |
| conflicting_paths | False | False | 296 | -296 |
| symmetric_fork | False | False | 295 | -295 |
| twin_corridors | False | False | 294 | -294 |
| crack_barrier | False | False | 296 | -296 |
| nested_ambiguity | False | False | 297 | -297 |
