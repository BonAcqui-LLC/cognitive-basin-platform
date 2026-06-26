path = r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\04_TESTS\layer_b_conformance\test_local_core.py"
with open(path, "r") as f:
    content = f.read()

# Fix 1a: strict bonding test - bond_distance_sq should be 4 for strict test
# The current strict test has 9 (from bad fix), change to 4
old_strict_line = 'p["bond_distance_sq"] = 9'
new_strict_line = 'p["bond_distance_sq"] = 4'
# Only change the first occurrence (strict test)
idx = content.find(old_strict_line)
if idx >= 0:
    content = content[:idx] + new_strict_line + content[idx + len(old_strict_line):]
    print("Fixed strict bonding bond_distance_sq")
else:
    print("strict bonding fix not needed")

# Fix 2: test_equal_energy_lower_id_wins
old_test = '    def test_equal_energy_lower_id_wins(self):\n        rng = TraceRng(42)\n        p = fresh_params()\n        n1 = make_node(0, (1, 0, 0), energy=100000, pressure=20000)\n        n2 = make_node(1, (5, 0, 0), energy=100000, pressure=20000)\n        n3 = make_node(2, (3, 5, 0), energy=300000)\n        nodes = [n1, n2, n3]\n        result = run_step(nodes, p, rng=rng)\n        n1r = [n for n in result if n["id"] == 0][0]\n        n2r = [n for n in result if n["id"] == 1][0]\n        moved = n1r["pos"] != (1, 0, 0) or n2r["pos"] != (5, 0, 0)\n        self.assertTrue(moved, "At least one node should have moved")'

new_test = '''    def test_equal_energy_lower_id_wins(self):
        rng = TraceRng(42)
        p = fresh_params()
        p["gamma_fallback_ppm"] = 1000000  # always fallback
        # n1 at (2,0,0) dir +x, n2 at (4,0,0) dir -x, both target (3,0,0)
        n1 = make_node(0, (2, 0, 0), energy=100000, pressure=20000, direction=(1, 0, 0))
        n2 = make_node(1, (4, 0, 0), energy=100000, pressure=20000, direction=(-1, 0, 0))
        nodes = [n1, n2]
        result = run_step(nodes, p, rng=rng)
        n1r = [n for n in result if n["id"] == 0][0]
        n2r = [n for n in result if n["id"] == 1][0]
        # n1 (lower id) should win contested target (3,0,0)
        if n1r["alive"]:
            self.assertEqual(n1r["pos"], (3, 0, 0),
                             "Lower id node should win contested target")'''

if old_test in content:
    content = content.replace(old_test, new_test)
    print("Fixed equal energy test")
else:
    print("old_test not found - checking partial match")
    # Try partial
    for old_part in ['n1 = make_node(0, (1, 0, 0), energy=100000, pressure=20000)']:
        if old_part in content:
            print(f"  Found: {old_part[:50]}")
        else:
            print(f"  Not found: {old_part[:50]}")

with open(path, "w") as f:
    f.write(content)
print("Done")
