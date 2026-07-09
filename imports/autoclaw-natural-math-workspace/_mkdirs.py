import os

# Create output directories
base = r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE"
for d in ["05_RESULTS\frozen_v5", "06_REPORTS"]:
    path = os.path.join(base, d)
    os.makedirs(path, exist_ok=True)
    print(f"Created: {path}")
