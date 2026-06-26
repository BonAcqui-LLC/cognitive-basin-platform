import json
d = json.loads(open(r'C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\05_RESULTS\frozen_v5\donor_differential_results.json').read())
for c in d['part_c_deterministic']['cases']:
    if c['kind'] == 'det_local':
        print(f"{c['name']}: matched={c['matched']}, flags={c['flags']}")
        for div in c['divergences'][:3]:
            donor_s = str(div.get('donor', '?'))
            clean_s = str(div.get('clean', '?'))
            if len(donor_s) > 120: donor_s = donor_s[:120] + '...'
            if len(clean_s) > 120: clean_s = clean_s[:120] + '...'
            print(f"  {div['field']}: donor={donor_s} clean={clean_s}")
            if 'diffs' in div:
                for d2 in div['diffs'][:5]:
                    print(f"    {d2}")
        print()
