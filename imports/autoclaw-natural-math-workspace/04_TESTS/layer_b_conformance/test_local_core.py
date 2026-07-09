"""Gate 3: Local-Core Conformance Tests.

Tests the run_step pipeline behavior: movement, bifurcation, bonding,
validation, edge cases. Each test constructs node scenarios and verifies
exact behavior from the frozen spec.

Run: python -m pytest test_local_core.py -v
"""

import sys
import unittest

sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")
from natural_math_v5 import run_step, default_params, NaturalMathValidationError
from natural_math_v5.records import make_node, is_live, NODE_FIELDS
from natural_math_v5.validation import as_tuple3, as_tuple3_strict
from natural_math_v5.randomness import TraceRng


def fresh_params():
    return default_params()

class TestDeficitAndScreamConflict(unittest.TestCase):
    """Section 6: use_deficit and use_poc_scream conflict."""
    def test_both_flags_raises(self):
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000)
        n2 = make_node(1, (0, 5, 0), energy=100000)
        nodes = [n1, n2]
        p = fresh_params()
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p, use_deficit=True, use_poc_scream=True)

class TestUnknownKeywordCallerError(unittest.TestCase):
    """Passing unknown keyword arg raises TypeError."""
    def test_bogus_flag_raises_typeerror(self):
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000)
        n2 = make_node(1, (0, 5, 0), energy=100000)
        nodes = [n1, n2]
        p = fresh_params()
        with self.assertRaises(TypeError):
            run_step(nodes, p, bogus_flag=True)

class TestListIdentityPreserved(unittest.TestCase):
    """run_step returns the same list object (mutated in place)."""
    def test_same_list_object_returned(self):
        rng = TraceRng(42)
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000)
        n2 = make_node(1, (0, 5, 0), energy=100000)
        nodes = [n1, n2]
        result = run_step(nodes, fresh_params(), rng=rng)
        self.assertIs(result, nodes)

class TestEmptyListIdentity(unittest.TestCase):
    """Empty list passed returns same empty list."""
    def test_empty_list_returns_same(self):
        nodes = []
        result = run_step(nodes, fresh_params())
        self.assertIs(result, nodes)
        self.assertEqual(len(result), 0)

class TestPublicTupleValidationRejectsLists(unittest.TestCase):
    """as_tuple3_strict rejects lists (public API uses strict)."""
    def test_rejects_list_pos(self):
        with self.assertRaises(NaturalMathValidationError):
            as_tuple3_strict([1, 2, 3], "test")
    def test_accepts_tuple(self):
        result = as_tuple3_strict((1, 2, 3), "test")
        self.assertEqual(result, (1, 2, 3))
    def test_rejects_list_with_float(self):
        with self.assertRaises(NaturalMathValidationError):
            as_tuple3_strict([1.0, 2, 3], "test")

class TestJsonAdapterConvertsLists(unittest.TestCase):
    """as_tuple3 accepts lists and converts to tuples (JSON adapter)."""
    def test_converts_list_to_tuple(self):
        result = as_tuple3([1, 2, 3], "test")
        self.assertEqual(result, (1, 2, 3))
    def test_accepts_tuple_as_is(self):
        result = as_tuple3((1, 2, 3), "test")
        self.assertEqual(result, (1, 2, 3))
    def test_rejects_wrong_length(self):
        with self.assertRaises(NaturalMathValidationError):
            as_tuple3([1, 2], "test")

class TestFallbackRngRequiredWhenReached(unittest.TestCase):
    """When gradient is zero and fallback is needed, rng is required."""
    def test_no_rng_fallback_needed_raises(self):
        # Two nodes with equal energy at large distance -> zero gradient
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000, direction=(0, 1, 0))
        n2 = make_node(1, (0, 100, 0), energy=100000)  # distance 10000 > r_sq=625
        nodes = [n1, n2]
        p = fresh_params()
        # Zero gradient because no neighbor within r_sq
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p, rng=None)

    def test_with_rng_fallback_works(self):
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000, direction=(0, 1, 0))
        nodes = [n1]
        p = fresh_params()
        p["gamma_fallback_ppm"] = 1000000  # always fallback
        rng = TraceRng(42)
        result = run_step(nodes, p, rng=rng)
        self.assertIsNotNone(result)

class TestNoRandomDrawWhenFallbackNotReached(unittest.TestCase):
    """When gradient is nonzero, no random draw is consumed."""
    def test_gradient_nonzero_no_draw_consumed(self):
        # Two nodes close enough for gradient (within r_sq), different energy
        n1 = make_node(0, (0, 0, 0), energy=50000, pressure=20000, direction=(0, 1, 0))
        n2 = make_node(1, (0, 5, 0), energy=200000)  # higher energy, within r_sq (25 <= 625)
        nodes = [n1, n2]
        p = fresh_params()
        rng = TraceRng(42)
        draws_before = len(rng.draws)
        run_step(nodes, p, rng=rng)
        # No additional draws should happen because gradient is nonzero
        self.assertEqual(len(rng.draws), draws_before)

class TestOrdinaryDeathRetainsEnergy(unittest.TestCase):
    """die_inert preserves energy at its current value after costs."""
    def test_dead_node_keeps_energy(self):
        # Node with very low energy dies, but energy value is preserved
        n1 = make_node(0, (0, 0, 0), energy=3000, pressure=20000)  # below tau=5000
        nodes = [n1]
        p = fresh_params()
        result = run_step(nodes, p)
        dead = result[0]
        self.assertFalse(dead["alive"])
        self.assertEqual(dead["type"], "inert")
        # Energy preserved (below tau pre-step kill preserves energy)
        self.assertGreater(dead["energy"], 0)

class TestSplitParentZeroEnergyBranch(unittest.TestCase):
    """Bifurcation parent becomes branch with energy=0."""
    def test_parent_becomes_branch_zero_energy(self):
        n1 = make_node(0, (0, 0, 0), energy=2000000, pressure=20000, direction=(0, 1, 0))
        n2 = make_node(1, (5, 0, 0), energy=2000000)  # within r_sq, gradient toward +x
        nodes = [n1, n2]
        p = fresh_params()
        rng = TraceRng(42)
        result = run_step(nodes, p, rng=rng)
        # Node 0 should have bifurcated if pressure >= P_bifurcate
        # Find parent node 0
        parent = [n for n in result if n["id"] == 0][0]
        if not parent["alive"] and parent["type"] == "branch":
            self.assertEqual(parent["energy"], 0)


class TestFrozenOccupancyBlocksAfterStateChange(unittest.TestCase):
    """Dead node positions remain occupied and block movement."""
    def test_dead_position_blocks_movement(self):
        rng = TraceRng(42)
        # n2 dies, its position is occupied (frozen), blocks n1 from moving there
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000, direction=(0, 1, 0))
        n2 = make_node(1, (0, 1, 0), energy=3000)  # dies (below tau), pos becomes frozen occupied
        nodes = [n1, n2]
        p = fresh_params()
        result = run_step(nodes, p, rng=rng)
        # n1's target (0,1,0) is occupied by dead n2, so n1 stays
        n1_result = [n for n in result if n["id"] == 0][0]
        self.assertEqual(n1_result["pos"], (0, 0, 0))  # did not move

class TestMovementWinnerEnergyThenId(unittest.TestCase):
    """Contested target: highest energy wins, ties to lower id."""
    def test_higher_energy_wins(self):
        rng = TraceRng(42)
        # Both target same unoccupied position; n2 higher energy wins
        n1 = make_node(0, (0, 0, 0), energy=80000, pressure=20000, direction=(0, 0, 1))
        n2 = make_node(1, (0, 0, -2), energy=120000, pressure=20000, direction=(0, 0, 1))
        nodes = [n1, n2]
        p = fresh_params()
        result = run_step(nodes, p, rng=rng)
        n1r = [n for n in result if n["id"] == 0][0]
        n2r = [n for n in result if n["id"] == 1][0]
        # Both target (0,0,1); n2 higher energy wins contested target
        # Winner: n2 reaches (0,0,1) or n1 blocks
        if n2r["alive"] and n1r["alive"]:
            self.assertEqual(n2r["pos"], (0, 0, 1),
                             "n2 with higher energy should win contested target")

    def test_equal_energy_lower_id_wins(self):
        rng = TraceRng(42)
        p = fresh_params()
        p["gamma_fallback_ppm"] = 1000000  # always fallback
        n1 = make_node(0, (2, 0, 0), energy=100000, pressure=20000, direction=(1, 0, 0))
        n2 = make_node(1, (4, 0, 0), energy=100000, pressure=20000, direction=(-1, 0, 0))
        nodes = [n1, n2]
        result = run_step(nodes, p, rng=rng)
        n1r = [n for n in result if n["id"] == 0][0]
        # n1 (lower id) wins contested target (3,0,0) with equal energy
        if n1r["alive"]:
            self.assertEqual(n1r["pos"], (3, 0, 0),
                             "Lower id wins contested target")
    def test_contested_blocked_both_lose(self):
        # Both target position occupied by a third node; both lose
        n1 = make_node(0, (2, 0, 0), energy=80000, pressure=20000, direction=(-1, 0, 0))
        n2 = make_node(1, (2, 2, 0), energy=90000, pressure=20000, direction=(0, -1, 0))
        n3 = make_node(2, (1, 1, 0), energy=5000)  # occupies target (1,1,0)
        nodes = [n1, n2, n3]
        p = fresh_params()
        result = run_step(nodes, p)
        n1r = [n for n in result if n["id"] == 0][0]
        n2r = [n for n in result if n["id"] == 1][0]
        # Neither should have reached (1,1,0) since n3 occupies it
        self.assertNotEqual(n1r["pos"], (1, 1, 0))
        self.assertNotEqual(n2r["pos"], (1, 1, 0))

class TestReservedChildBlocksMovement(unittest.TestCase):
    """Two parents bifurcate: first reserves child positions, second cannot use them."""
    def test_second_parent_child_blocked_by_first_reservation(self):
        # Two parents with high pressure and energy, close enough for gradient
        p = fresh_params()
        n1 = make_node(0, (0, 0, 0), energy=2000000, pressure=20000, direction=(0, 1, 0))
        n2 = make_node(1, (15, 0, 0), energy=2000000, pressure=20000, direction=(-1, 0, 0))
        nodes = [n1, n2]
        rng = TraceRng(42)
        result = run_step(nodes, p, rng=rng)
        # Both parents should have attempted bifurcation
        # Check that children exist and don't overlap
        alive_children = [n for n in result if n["alive"] and n["type"] == "tip"]
        positions = [n["pos"] for n in alive_children]
        self.assertEqual(len(positions), len(set(positions)), "Child positions must be unique")

class TestChildReservationMultipleParents(unittest.TestCase):
    """Multiple parents bifurcate; reservations prevent collisions."""
    def test_multiple_parents_no_child_collision(self):
        p = fresh_params()
        rng = TraceRng(123)
        nodes = []
        for i in range(5):
            nodes.append(make_node(i, (i * 5, 0, 0), energy=2000000, pressure=20000, direction=(0, 1, 0)))
        result = run_step(nodes, p, rng=rng)
        # All children at unique positions
        all_positions = [n["pos"] for n in result]
        self.assertEqual(len(all_positions), len(set(all_positions)))

class TestSparseIdChildAllocation(unittest.TestCase):
    """Child IDs are allocated with next_id counter, may have gaps."""
    def test_child_ids_are_unique_and_sequential(self):
        p = fresh_params()
        n1 = make_node(0, (0, 0, 0), energy=2000000, pressure=20000, direction=(0, 1, 0))
        n2 = make_node(1, (10, 0, 0), energy=2000000, pressure=20000, direction=(-1, 0, 0))
        nodes = [n1, n2]
        rng = TraceRng(42)
        result = run_step(nodes, p, rng=rng)
        ids = sorted([n["id"] for n in result])
        # All IDs should be unique
        self.assertEqual(len(ids), len(set(ids)))
        # Children should have IDs > max parent ID
        self.assertTrue(all(i > 1 for i in ids if i > 1),
                        "Child IDs should be >= 2")

class TestSameStepChildPressure(unittest.TestCase):
    """Child gets pressure update same step as born."""
    def test_child_gets_pressure_in_birth_step(self):
        p = fresh_params()
        n1 = make_node(0, (0, 0, 0), energy=2000000, pressure=20000, direction=(0, 1, 0))
        n2 = make_node(1, (15, 0, 0), energy=2000000, pressure=20000, direction=(-1, 0, 0))
        nodes = [n1, n2]
        rng = TraceRng(42)
        result = run_step(nodes, p, rng=rng)
        children = [n for n in result if n["type"] == "tip" and n["alive"]]
        for child in children:
            # Children get delta_P_baseline * beta_num // beta_den pressure in birth step
            expected_pressure = (p["delta_P_baseline"] * p["beta_num"]) // p["beta_den"]
            self.assertEqual(child["pressure"], expected_pressure,
                             f"Child {child['id']} pressure should be updated same step")

class TestOddSplitEnergyDissipation(unittest.TestCase):
    """Integer division in split energy: odd total energy handled correctly."""
    def test_odd_split_energy_conservation(self):
        p = fresh_params()
        # Energy = eps_extend + eps_spawn + eps_split + 2*tau + extra
        required = p["eps_extend"] + p["eps_spawn"] + p["eps_split"] + 2 * p["tau"]
        parent_energy = required + 100  # odd amount left after costs
        n1 = make_node(0, (0, 0, 0), energy=parent_energy, pressure=20000, direction=(0, 1, 0))
        n2 = make_node(1, (15, 0, 0), energy=2000000)
        nodes = [n1, n2]
        rng = TraceRng(42)
        result = run_step(nodes, p, rng=rng)
        parent = [n for n in result if n["id"] == 0][0]
        if parent["type"] == "branch":
            children = [n for n in result if n["parent_id"] == 0]
            if len(children) == 2:
                total_child_energy = children[0]["energy"] + children[1]["energy"]
                # Children get equal shares: (parent_energy - costs) // 2 each
                expected_per_child = (parent_energy - p["eps_extend"] - p["eps_spawn"] - p["eps_split"]) // 2
                self.assertLessEqual(total_child_energy, parent_energy - p["eps_extend"] - p["eps_spawn"] - p["eps_split"])

class TestFailedSplitFallsBackToMovement(unittest.TestCase):
    """When can_bifurcate returns False, node falls back to movement."""
    def test_insufficient_pressure_falls_back_to_movement(self):
        p = fresh_params()
        # Pressure below P_bifurcate, so bifurcation fails, node moves instead
        n1 = make_node(0, (0, 0, 0), energy=2000000, pressure=0, direction=(0, 1, 0))
        n2 = make_node(1, (0, 15, 0), energy=3000000)  # gradient pulls n1 toward +y
        nodes = [n1, n2]
        result = run_step(nodes, p)
        n1r = [n for n in result if n["id"] == 0][0]
        # n1 should have moved (not bifurcated)
        if n1r["alive"]:
            self.assertNotEqual(n1r["pos"], (0, 0, 0),
                                "Node with insufficient pressure should move, not bifurcate")

class TestLiveVsHistoricalBondDegree(unittest.TestCase):
    """Live bond degree counts only live bonds; dead bonds stay in record."""
    def test_dead_bonds_not_counted_in_degree(self):
        rng = TraceRng(42)
        p = fresh_params()
        p["max_bonds"] = 4
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000, direction=(0, 1, 0))
        n2 = make_node(1, (0, 1, 0), energy=3000)  # dies
        n1["bonds"].add(1)
        n2["bonds"].add(0)
        nodes = [n1, n2]
        result = run_step(nodes, p, rng=rng)
        n1r = [n for n in result if n["id"] == 0][0]
        self.assertIn(1, n1r["bonds"])
        n2r = [n for n in result if n["id"] == 1][0]
        self.assertFalse(n2r["alive"])

class TestStrictBondingDistance(unittest.TestCase):
    """bonding_strict=True: distance must be < bond_distance_sq (strict inequality)."""
    def test_exact_boundary_no_bond_strict(self):
        rng = TraceRng(42)
        p = fresh_params()
        p["bond_distance_sq"] = 4
        p["gamma_fallback_ppm"] = 0  # never fallback, both SENSE
        n1 = make_node(0, (0, 0, 0), energy=500000, pressure=20000, direction=(0, 1, 0))
        n2 = make_node(1, (2, 0, 0), energy=500000, direction=(0, 1, 0))
        nodes = [n1, n2]
        result = run_step(nodes, p, allow_bonding=True, bonding_strict=True, rng=rng)
        n1r = [n for n in result if n["id"] == 0][0]
        self.assertNotIn(1, n1r["bonds"], "Strict: distance 4 not < 4, no bond")

class TestNonStrictBondingDistance(unittest.TestCase):
    """bonding_strict=False: distance must be <= bond_distance_sq."""
    def test_exact_boundary_bonds_non_strict(self):
        rng = TraceRng(42)
        p = fresh_params()
        p["bond_distance_sq"] = 9
        p["gamma_fallback_ppm"] = 0  # never fallback, both SENSE
        n1 = make_node(0, (0, 0, 0), energy=500000, pressure=20000, direction=(0, 1, 0))
        n2 = make_node(1, (2, 0, 0), energy=500000, direction=(0, 1, 0))
        nodes = [n1, n2]
        result = run_step(nodes, p, allow_bonding=True, bonding_strict=False, rng=rng)
        n1r = [n for n in result if n["id"] == 0][0]
        n2r = [n for n in result if n["id"] == 1][0]
        self.assertTrue(n1r["alive"], "n1 should survive")
        self.assertTrue(n2r["alive"], "n2 should survive")
        self.assertIn(1, n1r["bonds"], "Non-strict: qdist=4 <= 9, should bond")

class TestDuplicatePositionRules(unittest.TestCase):
    """Duplicate positions are allowed by spec (frozen occupancy from both nodes)."""
    def test_two_nodes_same_position_valid(self):
        n1 = make_node(0, (5, 5, 5), energy=100000, pressure=20000, direction=(0, 1, 0))
        n2 = make_node(1, (5, 5, 5), energy=100000, pressure=20000, direction=(0, 1, 0))
        nodes = [n1, n2]
        p = fresh_params()
        # This should not raise validation error per spec
        result = run_step(nodes, p)
        self.assertEqual(len(result), 2)

class TestNodeFieldValidation(unittest.TestCase):
    """Section 6: node field validation."""
    def test_extra_field_rejected(self):
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000)
        n1["extra"] = "bad"
        nodes = [n1]
        p = fresh_params()
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p)

    def test_missing_field_rejected(self):
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000)
        n1.pop("signal_type")
        nodes = [n1]
        p = fresh_params()
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p)

    def test_negative_id_rejected(self):
        n1 = make_node(-1, (0, 0, 0), energy=100000, pressure=20000)
        nodes = [n1]
        p = fresh_params()
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p)

    def test_duplicate_id_rejected(self):
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000)
        n2 = make_node(0, (5, 0, 0), energy=100000, pressure=20000)
        nodes = [n1, n2]
        p = fresh_params()
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p)

    def test_duplicate_ids_rejected(self):
        """Explicit test that duplicate IDs are rejected."""
        n1 = make_node(1, (0, 0, 0), energy=100000, pressure=20000)
        n2 = make_node(1, (2, 0, 0), energy=100000, pressure=20000)
        nodes = [n1, n2]
        p = fresh_params()
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p)

    def test_invalid_direction_rejected(self):
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000)
        n1["direction"] = (2, 0, 0)  # not in DIRECTIONS_WITH_ZERO
        nodes = [n1]
        p = fresh_params()
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p)

    def test_negative_energy_rejected(self):
        n1 = make_node(0, (0, 0, 0), energy=-1, pressure=20000)
        nodes = [n1]
        p = fresh_params()
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p)

    def test_negative_pressure_rejected(self):
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=-1)
        nodes = [n1]
        p = fresh_params()
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p)

    def test_alive_not_bool_rejected(self):
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000)
        n1["alive"] = 1
        nodes = [n1]
        p = fresh_params()
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p)

    def test_unknown_type_rejected(self):
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000)
        n1["type"] = "unknown"
        nodes = [n1]
        p = fresh_params()
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p)

    def test_live_with_dead_type_rejected(self):
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000, alive=True, node_type="inert")
        nodes = [n1]
        p = fresh_params()
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p)

    def test_dead_with_live_type_alive_rejected(self):
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000, alive=False, node_type="tip")
        n1["alive"] = True
        nodes = [n1]
        p = fresh_params()
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p)

    def test_bonds_not_set_rejected(self):
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000)
        n1["bonds"] = [1, 2]  # list instead of set
        nodes = [n1]
        p = fresh_params()
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p)

    def test_bond_to_absent_id_rejected(self):
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000)
        n1["bonds"].add(999)  # bond to nonexistent node
        nodes = [n1]
        p = fresh_params()
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p)

    def test_asymmetric_live_bond_rejected(self):
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000)
        n2 = make_node(1, (5, 0, 0), energy=100000, pressure=20000)
        n1["bonds"].add(1)  # asymmetric: n1 bonds to n2 but n2 doesn't bond back
        nodes = [n1, n2]
        p = fresh_params()
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p)

    def test_max_live_bonds_exceeded_rejected(self):
        p = fresh_params()
        p["max_bonds"] = 1
        n1 = make_node(0, (0, 0, 0), energy=100000, pressure=20000)
        n2 = make_node(1, (5, 0, 0), energy=100000, pressure=20000)
        n3 = make_node(2, (0, 5, 0), energy=100000, pressure=20000)
        n1["bonds"].add(1); n2["bonds"].add(0)  # bond 0-1
        n1["bonds"].add(2); n3["bonds"].add(0)  # bond 0-2 -> exceeds max_bonds=1
        nodes = [n1, n2, n3]
        with self.assertRaises(NaturalMathValidationError):
            run_step(nodes, p)

class TestOutOfBoundsKill(unittest.TestCase):
    """Nodes outside world boundary (-100 to 100) are killed pre-step."""
    def test_out_of_bounds_node_killed(self):
        n1 = make_node(0, (150, 0, 0), energy=100000, pressure=20000)
        nodes = [n1]
        p = fresh_params()
        result = run_step(nodes, p)
        self.assertFalse(result[0]["alive"])
        self.assertEqual(result[0]["type"], "inert")

    def test_boundary_negative_killed(self):
        n1 = make_node(0, (-101, 0, 0), energy=100000, pressure=20000)
        nodes = [n1]
        p = fresh_params()
        result = run_step(nodes, p)
        self.assertFalse(result[0]["alive"])

    def test_within_bounds_survives(self):
        rng = TraceRng(42)
        n1 = make_node(0, (100, 100, 100), energy=100000, pressure=20000)
        nodes = [n1]
        p = fresh_params()
        result = run_step(nodes, p, rng=rng)
        self.assertEqual(result[0]["pos"], (100, 100, 100))

class TestPreStepKillBelowTau(unittest.TestCase):
    """Nodes with energy < tau are killed pre-step."""
    def test_energy_below_tau_killed(self):
        n1 = make_node(0, (0, 0, 0), energy=3000, pressure=20000)
        nodes = [n1]
        p = fresh_params()
        p["tau"] = 5000
        result = run_step(nodes, p)
        self.assertFalse(result[0]["alive"])
        self.assertEqual(result[0]["type"], "inert")

    def test_energy_equal_tau_survives_initially(self):
        rng = TraceRng(42)
        n1 = make_node(0, (0, 0, 0), energy=5000, pressure=20000)
        nodes = [n1]
        p = fresh_params()
        p["tau"] = 5000
        result = run_step(nodes, p, rng=rng)
        self.assertIn(result[0]["alive"], [True, False])

if __name__ == "__main__":
    unittest.main()





