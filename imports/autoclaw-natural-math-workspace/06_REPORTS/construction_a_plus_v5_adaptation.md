# Construction A+ v5 — Adaptation for Natural Math Integer States

## Overview

This module adapts **Construction A+ (Π_A+)** to read **Natural Math v5 integer attractor states** and convert them into discrete **SymLan glyphs**.

### Key Changes from v3.6 Era

| Aspect | v3.6 (Original) | v5 (Adapted) |
|--------|-----------------|--------------|
| Input | Continuous time-series data | Integer node states |
| State representation | Floating-point positions/energy | Discrete integer coordinates |
| Attractor detection | Time-series clustering | Final state topology |
| Feature extraction | 7D continuous features | Morphological signature |

## Module Structure

```
construction_a_plus_v5/
├── __init__.py          # Main Π_A+ operator implementation
└── test_ca_plus_v5.py   # Integration tests with Natural Math v5
```

## Core Components

### 1. Attractor Signature (`compute_attractor_signature`)

Extracts morphological metrics from v5 node states:
- `alive_count`: Number of live nodes
- `component_count`: Connected components via bonds
- `total_energy`: Sum of node energies
- `energy_variance`: Energy distribution spread
- `bond_density`: Ratio of actual to possible bonds
- `spatial_extent`: 3D bounding box size
- `center_of_mass`: Weighted position center
- `topology_hash`: Deterministic hash of structure

### 2. PEFP(k) — Persistent Expression Fingerprint

Extracts k salient features and applies **θ:auto** (automatic ternary quantization):

**Features (k=9 default):**
0. alive_count (normalized)
1. component_count
2. total_energy (log-scaled)
3. energy_variance (log-scaled)
4. bond_density
5. spatial_extent_x
6. spatial_extent_y
7. spatial_extent_z
8. topology_hash prefix (numeric)

**Quantization strategy:**
- Compute 33rd and 67th percentiles across feature values
- Map: below p33 → -1, between p33-p67 → 0, above p67 → +1

### 3. Polarity Bit (τ_E)

Single bit indicating energy-positive vs energy-negative attractor:
```
polarity = 1 if (avg_energy > components × baseline) else 0
```

### 4. Glyph Encoding

**Format:** `glyph_id = polarity × 3^k + ternary_value`

**Range for k=9:** 0 to 39,365 (2 × 3^9 = 39,366 total glyphs)

## Usage Examples

### Single Glyph Extraction

```python
from natural_math_v5 import cluster
from construction_a_plus_v5 import glyph_from_cluster_run

# Run Natural Math v5 simulation
result = cluster.run_cluster(seed=42, steps=140)

# Extract SymLan glyph
glyph = glyph_from_cluster_run(result, k=9)

print(f"Glyph ID: {glyph['glyph_id']}")
print(f"Polarity: {glyph['polarity_bit']}")
print(f"PEFP: {glyph['pefp_digits']}")
```

### Batch Processing

```python
from construction_a_plus_v5 import extract_glyphs_from_batch, check_vocabulary_collisions

# Run multiple simulations
results = []
for seed in [1, 42, 100, 256, 1000]:
    r = cluster.run_cluster(seed=seed, steps=140)
    r["seed"] = seed
    results.append(r)

# Extract all glyphs
glyphs = extract_glyphs_from_batch(results, k=9)

# Analyze vocabulary
analysis = check_vocabulary_collisions(glyphs)
print(f"Unique glyphs: {analysis['unique_glyphs']}")
print(f"Entropy: {analysis['vocabulary_entropy_bits']:.3f} bits")
print(f"Collision-free: {analysis['is_collision_free']}")
```

### Round-Trip Decoding

```python
from construction_a_plus_v5 import decode_glyph

glyph_id = 30457
polarity, pefp_digits = decode_glyph(glyph_id, k=9)
# polarity = 1
# pefp_digits = [0, 0, 1, 1, 0, -1, -1, -1, 0]
```

## Test Results

Running `test_ca_plus_v5.py`:

```
TEST 1: Single Glyph Extraction
✓ Seed 42 → glyph_id=30457, polarity=1, PEFP=[0,0,1,1,0,-1,-1,-1,0]
✓ Round-trip decode successful

TEST 2: Batch Extraction (5 seeds)
✓ Unique glyphs: 2
✓ Entropy: 0.722 bits

TEST 3: Different K Values
✓ k=3: 54 max glyphs
✓ k=5: 486 max glyphs
✓ k=7: 4,374 max glyphs
✓ k=9: 39,366 max glyphs
```

## Integration Points

### With Natural Math v5

```python
# Direct integration with cluster runner
from natural_math_v5.cluster import run_cluster
from construction_a_plus_v5 import glyph_from_cluster_run

result = run_cluster(seed=42, steps=140)
glyph = glyph_from_cluster_run(result)
```

### With Cognitive Basin (Future)

When Cognitive Basin produces settled attractor basins:

```python
# Pseudocode for future integration
from cognitive_basin import get_settled_attractors
from construction_a_plus_v5 import extract_glyph_from_v5_state

attractors = get_settled_attractors(process_history)
for attractor in attractors:
    glyph = extract_glyph_from_v5_state(attractor.nodes)
```

### With SymLan Runtime (Future)

```python
# Pseudocode for SymLan vocabulary resolution
class SymLanType:
    def resolve(self, substrate_state):
        glyph = glyph_from_cluster_run(substrate_state)
        self.vocabulary = [glyph['glyph_id']]
        return ResolvedType(self.vocabulary)
```

## Design Decisions

### Why 9 Ternary Digits?

- Matches SymLan v1.0 specification
- Provides 39,366 possible glyphs (sufficient for rich vocabulary)
- Balances expressiveness with collision resistance

### Why Automatic Quantization (θ:auto)?

- Adapts to substrate characteristics without manual tuning
- Enables cross-substrate comparison (proteinoid, fungal, abiotic)
- Preserves relative ordering of features

### Why Topology Hash?

- Captures structural information beyond simple metrics
- Provides deterministic fingerprint for reproducibility
- Enables detection of isomorphic attractors

## Next Steps for Baby-AI Build

1. **Stage 1-5:** Natural Math + Cognitive Basin produce stable attractors
2. **Stage 6:** Verify attractor persistence across replay
3. **Stage 7+:** Apply Construction A+ to extract vocabulary
4. **Stage 8:** Integrate with SymLan type system

## References

- SymLan v1.0 Language Specification
- Construction A+ Technical Accounting (full pipeline)
- Natural Math v5 Reference Implementation
- Baby-AI Layered Build Map
