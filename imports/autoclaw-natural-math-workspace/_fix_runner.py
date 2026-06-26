import re

path = r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\_stage1_runner.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Add canonical spec path constant after RESULTS_DIR definition
old = "RESULTS_DIR.mkdir(parents=True, exist_ok=True)"
new = """RESULTS_DIR.mkdir(parents=True, exist_ok=True)
CANON_SPEC = Path(r"C:\\_MASTER_LIBRARY\\01_CANON\\01_NATURAL_MATH_V5\\Natural Math v5 - Status Frozen Int.txt")"""
content = content.replace(old, new)

# Update sha256 check in run_integer_fixtures and run_cluster_fixtures
# Fix: try fixture spec path, fall back to canonical
old_check = """    spec_path = Path(suite["spec"]["path"])
    spec_hash_actual = sha256(spec_path) if spec_path.exists() else None
    spec_hash_expected = suite["spec"]["sha256"]

    cases = []
    all_passed = spec_hash_actual == spec_hash_expected"""

# Function to resolve spec path
new_check = """    # Resolve spec path: try fixture path, fall back to canonical
    spec_path = Path(suite["spec"]["path"])
    if not spec_path.exists():
        spec_path = CANON_SPEC
    spec_hash_actual = sha256(spec_path) if spec_path.exists() else None
    spec_hash_expected = suite["spec"]["sha256"]

    cases = []
    all_passed = spec_hash_actual == spec_hash_expected"""

# Replace both occurrences (integer and cluster)
content = content.replace(old_check, new_check)
# The second occurrence uses same pattern
# Let's verify only 2 occurrences exist
count = content.count("spec_path = Path(suite")
print(f"Found {count} spec_path assignments")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Runner updated with canonical spec path fallback")
