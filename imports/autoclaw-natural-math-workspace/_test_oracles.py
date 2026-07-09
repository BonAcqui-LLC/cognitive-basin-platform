import json, sys, os
sys.path.insert(0, '02_REFERENCE_IMPLEMENTATION')
from natural_math_v5 import run_step, run_cluster, default_params
from natural_math_v5.serialization import nodes_to_json

base = r'C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5\ORACLE_FIXTURES'

# Load integer fixtures
with open(os.path.join(base, 'natural_math_integer_oracle_fixtures.json')) as f:
    int_fixtures = json.load(f)
print(f'Loaded {len(int_fixtures)} integer fixtures')

passed = 0
failed = 0

for i, fx in enumerate(int_fixtures):
    name = fx.get('name', f'fixture_{i}')
    inp = fx['input']
    nodes_original = inp['nodes']
    steps = inp.get('steps', 1)

    # Convert to internal format
    nodes = []
    for n in nodes_original:
        nd = dict(n)
        nd['pos'] = tuple(nd['pos'])
        nd['direction'] = tuple(nd['direction'])
        nd['bonds'] = set(nd.get('bonds', []))
        nodes.append(nd)

    params = default_params()
    try:
        for s in range(steps):
            run_step(nodes, params)
        # Convert back for comparison
        result = nodes_to_json(nodes)
        # Check against expected if present
        expected = fx.get('expected_nodes')
        if expected:
            # Compare key fields
            exp_by_id = {n['id']: n for n in expected}
            res_by_id = {n['id']: n for n in result}
            match = True
            for nid in exp_by_id:
                if nid not in res_by_id:
                    match = False
                    break
                e = exp_by_id[nid]
                r = res_by_id[nid]
                if e.get('alive') != r.get('alive'):
                    match = False
                if e.get('pos') != r.get('pos'):
                    match = False
                if e.get('energy') != r.get('energy'):
                    match = False
            if match:
                passed += 1
                print(f'  PASS [{i}] {name}')
            else:
                failed += 1
                print(f'  FAIL [{i}] {name}')
        else:
            passed += 1
            print(f'  PASS [{i}] {name} (no expected)')
    except Exception as e:
        failed += 1
        print(f'  FAIL [{i}] {name}: {e}')

print(f'')
print(f'Integer fixtures: {passed}/{passed+failed} passed')
