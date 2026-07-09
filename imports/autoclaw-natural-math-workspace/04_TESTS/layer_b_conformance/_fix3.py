path = r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\04_TESTS\layer_b_conformance\test_local_core.py"
with open(path, "r") as f:
    lines = f.readlines()

# Find the test_equal_energy_lower_id_wins and replace the whole block
start = None
end = None
for i, line in enumerate(lines):
    if 'def test_equal_energy_lower_id_wins(self):' in line:
        start = i
    if start is not None and i > start and 'def test_' in line and 'test_equal_energy_lower_id_wins' not in line:
        end = i
        break

if start is not None and end is not None:
    new_block = [
        '    def test_equal_energy_lower_id_wins(self):\n',
        '        rng = TraceRng(42)\n',
        '        p = fresh_params()\n',
        '        p["gamma_fallback_ppm"] = 1000000  # always fallback\n',
        '        n1 = make_node(0, (2, 0, 0), energy=100000, pressure=20000, direction=(1, 0, 0))\n',
        '        n2 = make_node(1, (4, 0, 0), energy=100000, pressure=20000, direction=(-1, 0, 0))\n',
        '        nodes = [n1, n2]\n',
        '        result = run_step(nodes, p, rng=rng)\n',
        '        n1r = [n for n in result if n["id"] == 0][0]\n',
        '        # n1 (lower id) wins contested target (3,0,0) with equal energy\n',
        '        if n1r["alive"]:\n',
        '            self.assertEqual(n1r["pos"], (3, 0, 0),\n',
        '                             "Lower id wins contested target")\n',
    ]
    new_lines = lines[:start] + new_block + lines[end:]
    with open(path, "w") as f:
        f.writelines(new_lines)
    print(f"Replaced lines {start}-{end-1}")
else:
    print(f"Could not find test block: start={start}, end={end}")
