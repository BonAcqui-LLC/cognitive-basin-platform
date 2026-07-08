"""Construction A+ (Π_A+) — Vocabulary Readout Operator for Natural Math v5.

This module adapts Construction A+ to read Natural Math v5 integer attractor states
and convert them into discrete SymLan glyphs.

Glyph structure: 1 polarity bit + k ternary digits
Default k=9: 2 × 3^9 = 39,366 possible glyphs (range 0..39365)

Key components:
- PEFP(k): Persistent Expression Fingerprint with k ternary digits
- θ:auto: Automatic ternary quantization thresholds
- τ_E: Attractor polarity bit (1 bit)
"""

from __future__ import annotations

import hashlib
import math
from typing import Any


def compute_attractor_signature(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute attractor basin signature from v5 integer node states.
    
    Args:
        nodes: List of node dicts from Natural Math v5 final state
        
    Returns:
        Dictionary with attractor metrics suitable for glyph encoding
    """
    live_nodes = [n for n in nodes if n.get("alive", False)]
    
    if not live_nodes:
        return {
            "alive_count": 0,
            "component_count": 0,
            "total_energy": 0,
            "energy_variance": 0,
            "bond_density": 0.0,
            "spatial_extent": (0, 0, 0),
            "center_of_mass": (0, 0, 0),
            "topology_hash": "",
        }
    
    # Basic counts
    alive_count = len(live_nodes)
    total_energy = sum(n["energy"] for n in live_nodes)
    
    # Energy statistics
    avg_energy = total_energy // alive_count
    energy_variance = sum((n["energy"] - avg_energy) ** 2 for n in live_nodes) // alive_count
    
    # Bond density
    total_bonds = sum(len(n.get("bonds", set())) for n in live_nodes)
    max_possible_bonds = alive_count * (alive_count - 1) // 2
    bond_density = total_bonds / max_possible_bonds if max_possible_bonds > 0 else 0.0
    
    # Spatial extent and center of mass
    positions = [n["pos"] for n in live_nodes]
    min_coords = tuple(min(p[i] for p in positions) for i in range(3))
    max_coords = tuple(max(p[i] for p in positions) for i in range(3))
    spatial_extent = tuple(max_coords[i] - min_coords[i] for i in range(3))
    
    center_sum = tuple(sum(p[i] for p in positions) for i in range(3))
    center_of_mass = tuple(c // alive_count for c in center_sum)
    
    # Component count (connected components via bonds)
    component_count = _count_components(live_nodes)
    
    # Topology hash for reproducibility
    topology_hash = _compute_topology_hash(live_nodes)
    
    return {
        "alive_count": alive_count,
        "component_count": component_count,
        "total_energy": total_energy,
        "energy_variance": energy_variance,
        "bond_density": bond_density,
        "spatial_extent": spatial_extent,
        "center_of_mass": center_of_mass,
        "topology_hash": topology_hash,
    }


def _count_components(nodes: list[dict[str, Any]]) -> int:
    """Count connected components using union-find on bond graph."""
    if not nodes:
        return 0
    
    node_ids = {n["id"] for n in nodes}
    parent = {nid: nid for nid in node_ids}
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py
    
    for node in nodes:
        for bonded_id in node.get("bonds", set()):
            if bonded_id in node_ids:
                union(node["id"], bonded_id)
    
    # Count unique roots
    roots = {find(nid) for nid in node_ids}
    return len(roots)


def _compute_topology_hash(nodes: list[dict[str, Any]]) -> str:
    """Compute deterministic hash of attractor topology."""
    # Sort by id for determinism
    sorted_nodes = sorted(nodes, key=lambda n: n["id"])
    
    # Create canonical representation
    topo_data = []
    for node in sorted_nodes:
        record = {
            "id": node["id"],
            "pos": tuple(node["pos"]),
            "energy": node["energy"],
            "type": node.get("type", ""),
            "bonds": sorted(node.get("bonds", set())),
        }
        topo_data.append(record)
    
    # Hash the topology
    hasher = hashlib.sha256()
    hasher.update(str(topo_data).encode("utf-8"))
    return hasher.hexdigest()[:16]


def auto_ternary_quantize(values: list[float | int], k: int = 9) -> list[int]:
    """Automatic ternary quantization (θ:auto) for k features.
    
    Converts continuous or integer values into ternary digits {-1, 0, +1}.
    
    Strategy:
    - Compute global statistics across all values
    - Set thresholds at 33rd and 67th percentiles
    - Map: below p33 → -1, between p33-p67 → 0, above p67 → +1
    
    Args:
        values: List of numeric feature values
        k: Number of ternary digits to produce (default 9)
        
    Returns:
        List of k ternary digits in {-1, 0, +1}
    """
    if not values:
        return [0] * k
    
    # Pad or truncate to k values
    if len(values) < k:
        # Pad with zeros (neutral)
        values = list(values) + [0.0] * (k - len(values))
    elif len(values) > k:
        # Take first k
        values = list(values[:k])
    
    # Compute percentile thresholds
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    p33_idx = n // 3
    p67_idx = (2 * n) // 3
    
    threshold_low = sorted_vals[p33_idx] if n > 0 else 0
    threshold_high = sorted_vals[p67_idx] if n > 0 else 0
    
    # Quantize each value
    ternary_digits = []
    for v in values:
        if v < threshold_low:
            ternary_digits.append(-1)
        elif v > threshold_high:
            ternary_digits.append(1)
        else:
            ternary_digits.append(0)
    
    return ternary_digits


def compute_pefp(attractor_sig: dict[str, Any], k: int = 9) -> list[int]:
    """Persistent Expression Fingerprint (PEFP) with k ternary digits.
    
    Extracts k salient features from attractor signature and quantizes them.
    
    Features extracted (in order):
    0. alive_count (normalized)
    1. component_count
    2. total_energy (log-scaled)
    3. energy_variance (log-scaled)
    4. bond_density
    5. spatial_extent_x
    6. spatial_extent_y
    7. spatial_extent_z
    8. topology_hash prefix (numeric)
    
    Args:
        attractor_sig: Attractor signature dict from compute_attractor_signature
        k: Number of ternary digits (default 9)
        
    Returns:
        List of k ternary digits in {-1, 0, +1}
    """
    features = []
    
    # Feature 0: alive_count (normalize by typical max ~100)
    features.append(attractor_sig["alive_count"] / 100.0)
    
    # Feature 1: component_count (typically 1-10)
    features.append(attractor_sig["component_count"] / 5.0)
    
    # Feature 2: total_energy (log-scale)
    total_e = max(1, attractor_sig["total_energy"])
    features.append(math.log(total_e + 1) / 10.0)
    
    # Feature 3: energy_variance (log-scale)
    var_e = max(1, attractor_sig["energy_variance"])
    features.append(math.log(var_e + 1) / 10.0)
    
    # Feature 4: bond_density (already 0-1)
    features.append(attractor_sig["bond_density"])
    
    # Features 5-7: spatial extent (normalize by world size ~200)
    extent = attractor_sig["spatial_extent"]
    features.append(extent[0] / 200.0)
    features.append(extent[1] / 200.0)
    features.append(extent[2] / 200.0)
    
    # Feature 8+: topology hash prefix as numeric
    topo_hash = attractor_sig["topology_hash"]
    if topo_hash:
        hash_val = int(topo_hash[:8], 16) / (16 ** 8)
        features.append(hash_val)
    
    # Pad if needed
    while len(features) < k:
        features.append(0.0)
    
    # Apply automatic ternary quantization
    return auto_ternary_quantize(features, k)


def compute_polarity_bit(attractor_sig: dict[str, Any]) -> int:
    """Compute attractor polarity bit (τ_E).
    
    Polarity indicates whether the attractor is "energy-positive" or "energy-negative"
    relative to its structural complexity.
    
    Formula:
    - If (total_energy / alive_count) > (component_count * baseline), polarity = 1
    - Else polarity = 0
    
    Args:
        attractor_sig: Attractor signature dict
        
    Returns:
        Polarity bit (0 or 1)
    """
    alive = max(1, attractor_sig["alive_count"])
    components = attractor_sig["component_count"]
    total_energy = attractor_sig["total_energy"]
    
    avg_energy = total_energy / alive
    
    # Baseline: ~100 energy per component is "positive"
    baseline_per_component = 100
    threshold = components * baseline_per_component / alive if alive > 0 else 0
    
    return 1 if avg_energy > threshold else 0


def ternary_to_int(ternary_digits: list[int]) -> int:
    """Convert list of ternary digits to integer.
    
    Uses standard base-3 interpretation with digits in {-1, 0, +1}.
    Maps {-1, 0, +1} to {0, 1, 2} for computation.
    
    Args:
        ternary_digits: List of digits in {-1, 0, +1}, most significant first
        
    Returns:
        Integer representation
    """
    result = 0
    for digit in ternary_digits:
        # Map {-1, 0, +1} to {0, 1, 2}
        mapped = digit + 1
        result = result * 3 + mapped
    return result


def encode_glyph(pefp_digits: list[int], polarity_bit: int) -> int:
    """Encode complete glyph from PEFP digits and polarity bit.
    
    Glyph format: polarity_bit followed by k ternary digits
    Range: 0 to (2 × 3^k) - 1
    
    For k=9: range is 0 to 39,365
    
    Args:
        pefp_digits: List of k ternary digits from PEFP
        polarity_bit: Single bit (0 or 1)
        
    Returns:
        Integer glyph ID
    """
    k = len(pefp_digits)
    ternary_value = ternary_to_int(pefp_digits)
    
    # Glyph = polarity × 3^k + ternary_value
    glyph_id = polarity_bit * (3 ** k) + ternary_value
    
    return glyph_id


def decode_glyph(glyph_id: int, k: int = 9) -> tuple[int, list[int]]:
    """Decode glyph ID back to polarity and ternary digits.
    
    Args:
        glyph_id: Integer glyph ID
        k: Number of ternary digits (default 9)
        
    Returns:
        Tuple of (polarity_bit, list of k ternary digits)
    """
    max_ternary = 3 ** k
    
    polarity_bit = glyph_id // max_ternary
    ternary_value = glyph_id % max_ternary
    
    # Convert integer back to ternary digits
    digits = []
    temp = ternary_value
    for _ in range(k):
        remainder = temp % 3
        # Map {0, 1, 2} back to {-1, 0, +1}
        digits.append(remainder - 1)
        temp //= 3
    
    # Digits are in reverse order (least significant first)
    digits.reverse()
    
    return polarity_bit, digits


def extract_glyph_from_v5_state(
    nodes: list[dict[str, Any]],
    k: int = 9,
) -> dict[str, Any]:
    """Main entry point: extract SymLan glyph from Natural Math v5 state.
    
    This is the Π_A+ operator adapted for v5 integer states.
    
    Pipeline:
    1. Compute attractor signature from node states
    2. Compute PEFP(k) ternary digits
    3. Compute polarity bit τ_E
    4. Encode complete glyph
    
    Args:
        nodes: Final node list from Natural Math v5 run
        k: Number of ternary digits (default 9)
        
    Returns:
        Dictionary with:
        - glyph_id: Integer glyph ID (0..39365 for k=9)
        - polarity_bit: 0 or 1
        - pefp_digits: List of k ternary digits
        - attractor_signature: Full signature dict
        - metadata: Encoding parameters
    """
    # Step 1: Compute attractor signature
    attractor_sig = compute_attractor_signature(nodes)
    
    # Step 2: Compute PEFP
    pefp_digits = compute_pefp(attractor_sig, k)
    
    # Step 3: Compute polarity bit
    polarity_bit = compute_polarity_bit(attractor_sig)
    
    # Step 4: Encode glyph
    glyph_id = encode_glyph(pefp_digits, polarity_bit)
    
    return {
        "glyph_id": glyph_id,
        "polarity_bit": polarity_bit,
        "pefp_digits": pefp_digits,
        "attractor_signature": attractor_sig,
        "metadata": {
            "k": k,
            "max_glyphs": 2 * (3 ** k),
            "operator": "Π_A+",
            "version": "v5_integer_adapted",
        },
    }


def extract_glyphs_from_batch(
    batch_results: list[dict[str, Any]],
    k: int = 9,
    node_key: str = "nodes",
) -> list[dict[str, Any]]:
    """Extract glyphs from multiple v5 simulation results.
    
    Args:
        batch_results: List of result dicts, each containing node states
        k: Number of ternary digits
        node_key: Key in result dict where nodes are stored (default "nodes")
        
    Returns:
        List of glyph extraction results
    """
    results = []
    for i, result in enumerate(batch_results):
        nodes = result.get(node_key, [])
        glyph_result = extract_glyph_from_v5_state(nodes, k)
        glyph_result["batch_index"] = i
        glyph_result["seed"] = result.get("seed", None)
        results.append(glyph_result)
    
    return results


def check_vocabulary_collisions(glyph_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Check for collisions in extracted vocabulary.
    
    Args:
        glyph_results: List of glyph extraction results
        
    Returns:
        Dictionary with collision analysis
    """
    glyph_ids = [r["glyph_id"] for r in glyph_results]
    unique_glyphs = set(glyph_ids)
    
    collisions = {}
    for gid in unique_glyphs:
        count = glyph_ids.count(gid)
        if count > 1:
            collisions[gid] = count
    
    # Compute entropy if we have multiple glyphs
    entropy = 0.0
    if len(glyph_ids) > 0:
        total = len(glyph_ids)
        for gid in unique_glyphs:
            p = glyph_ids.count(gid) / total
            if p > 0:
                entropy -= p * math.log2(p)
    
    return {
        "total_samples": len(glyph_ids),
        "unique_glyphs": len(unique_glyphs),
        "collision_count": len(collisions),
        "collisions": collisions,
        "vocabulary_entropy_bits": entropy,
        "is_collision_free": len(collisions) == 0,
    }


# Convenience function for direct integration with cluster runner
def glyph_from_cluster_run(cluster_result: dict[str, Any], k: int = 9) -> dict[str, Any]:
    """Extract glyph directly from Natural Math v5 cluster run result.
    
    Args:
        cluster_result: Result dict from natural_math_v5.cluster.run_cluster()
        k: Number of ternary digits
        
    Returns:
        Glyph extraction result
    """
    nodes = cluster_result.get("nodes", [])
    return extract_glyph_from_v5_state(nodes, k)
