import json, pprint

with open(r'C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5\ORACLE_FIXTURES\natural_math_integer_oracle_fixtures.json') as f:
    d = json.load(f)

fxs = d['fixtures']
print(f'Total fixtures: {len(fxs)}')

# Inspect first 3
for i in range(3):
    fx = fxs[i]
    print(f'')
    print(f'--- Fixture {i}: {fx[\"name\"]} ---')
    print(f'  nodes count: {len(fx[\"nodes\"])}')
    print(f'  expected_nodes count: {len(fx[\"expected_nodes\"])}')
    print(f'  expected_draws count: {len(fx.get(\"expected_random_draws\", []))}')
    print(f'  flags: {fx.get(\"flags\", {})}')
    if fx['nodes']:
        n = fx['nodes'][0]
        print(f'  sample node: id={n[\"id\"]}, pos={n[\"pos\"]}, energy={n.get(\"energy\")}, alive={n.get(\"alive\")}')

# Look at a fixture with expected draws
for fx in fxs:
    if fx.get('expected_random_draws'):
        print(f'')
        print(f'Fixture with draws: {fx[\"name\"]}')
        print(f'  expected draws: {fx[\"expected_random_draws\"][:5]}... ({len(fx[\"expected_random_draws\"])} total)')
        break
