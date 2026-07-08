#!/usr/bin/env python3
"""Test Construction A+ v5 integration with Natural Math v5.

This script demonstrates extracting SymLan glyphs from Natural Math v5 cluster runs.
"""

import sys
sys.path.insert(0, '/workspace/imports/autoclaw-natural-math-workspace/02_REFERENCE_IMPLEMENTATION')

from natural_math_v5 import cluster
from construction_a_plus_v5 import (
    extract_glyph_from_v5_state,
    extract_glyphs_from_batch,
    check_vocabulary_collisions,
    glyph_from_cluster_run,
    decode_glyph,
)


def test_single_glyph_extraction():
    """Test extracting a glyph from a single v5 cluster run."""
    print("=" * 60)
    print("TEST 1: Single Glyph Extraction")
    print("=" * 60)
    
    # Run a small cluster simulation
    seed = 42
    result = cluster.run_cluster(seed=seed, steps=50)
    
    print(f"Seed: {seed}")
    print(f"Steps: 50")
    print(f"Alive nodes: {result['metrics']['alive_count']}")
    print(f"Components: {result['metrics']['component_count']}")
    print(f"Passed: {result['passed']}")
    
    # Extract glyph
    glyph_result = glyph_from_cluster_run(result, k=9)
    
    print(f"\nGlyph ID: {glyph_result['glyph_id']}")
    print(f"Polarity bit: {glyph_result['polarity_bit']}")
    print(f"PEFP digits: {glyph_result['pefp_digits']}")
    print(f"Attractor signature:")
    sig = glyph_result['attractor_signature']
    print(f"  - Alive count: {sig['alive_count']}")
    print(f"  - Component count: {sig['component_count']}")
    print(f"  - Total energy: {sig['total_energy']}")
    print(f"  - Bond density: {sig['bond_density']:.4f}")
    print(f"  - Spatial extent: {sig['spatial_extent']}")
    print(f"  - Topology hash: {sig['topology_hash']}")
    
    # Verify round-trip decoding
    polarity, digits = decode_glyph(glyph_result['glyph_id'], k=9)
    assert polarity == glyph_result['polarity_bit'], "Polarity mismatch in decode!"
    assert digits == glyph_result['pefp_digits'], "PEFP digits mismatch in decode!"
    print("\n✓ Round-trip decode successful")
    
    return glyph_result


def test_batch_extraction():
    """Test extracting glyphs from multiple seeds."""
    print("\n" + "=" * 60)
    print("TEST 2: Batch Glyph Extraction")
    print("=" * 60)
    
    seeds = [1, 42, 100, 256, 1000]
    results = []
    
    for seed in seeds:
        run_result = cluster.run_cluster(seed=seed, steps=50)
        run_result["seed"] = seed
        results.append(run_result)
    
    # Extract all glyphs
    glyph_results = extract_glyphs_from_batch(results, k=9)
    
    print(f"Processed {len(glyph_results)} simulations")
    print("\nGlyph vocabulary:")
    for gr in glyph_results:
        print(f"  Seed {gr['seed']:4d}: glyph_id={gr['glyph_id']:5d}, polarity={gr['polarity_bit']}, PEFP={gr['pefp_digits']}")
    
    # Check for collisions
    collision_analysis = check_vocabulary_collisions(glyph_results)
    
    print(f"\nVocabulary analysis:")
    print(f"  Total samples: {collision_analysis['total_samples']}")
    print(f"  Unique glyphs: {collision_analysis['unique_glyphs']}")
    print(f"  Collision count: {collision_analysis['collision_count']}")
    print(f"  Entropy: {collision_analysis['vocabulary_entropy_bits']:.3f} bits")
    print(f"  Collision-free: {collision_analysis['is_collision_free']}")
    
    return glyph_results, collision_analysis


def test_different_k_values():
    """Test glyph extraction with different k values."""
    print("\n" + "=" * 60)
    print("TEST 3: Different K Values")
    print("=" * 60)
    
    seed = 42
    result = cluster.run_cluster(seed=seed, steps=50)
    
    for k in [3, 5, 7, 9]:
        glyph_result = extract_glyph_from_v5_state(result["nodes"], k=k)
        max_glyphs = 2 * (3 ** k)
        print(f"k={k}: glyph_id={glyph_result['glyph_id']:6d}, max_possible={max_glyphs:6d}, PEFP={glyph_result['pefp_digits']}")
    
    return True


def main():
    """Run all tests."""
    print("Construction A+ v5 — Natural Math v5 Integration Test")
    print("=" * 60)
    
    try:
        # Test 1: Single extraction
        test_single_glyph_extraction()
        
        # Test 2: Batch extraction
        test_batch_extraction()
        
        # Test 3: Different k values
        test_different_k_values()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
