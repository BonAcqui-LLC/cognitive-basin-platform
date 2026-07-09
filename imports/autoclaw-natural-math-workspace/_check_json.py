import json
path = r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\05_RESULTS\frozen_v5\original_oracle_results.json"
with open(path) as f:
    data = json.load(f)
print("Overall:", data["overall_passed"])
print("Total fixtures:", data["total_fixtures"])
print("Passed:", data["passed_count"])
print("Integer passed:", data["integer_fixtures"]["passed"])
print("Cluster passed:", data["cluster_fixtures"]["passed"])
print("Fixes applied:", len(data["fixes_applied"]))
for fx in data["fixes_applied"]:
    print("  -", fx)
