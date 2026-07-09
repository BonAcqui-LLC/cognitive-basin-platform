import re

# ============================================================
# ISSUE 7: Fix core_step.py - remove bonding flag check
# ============================================================
path = r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION\natural_math_v5\core_step.py"
with open(path, "r", encoding="utf-8-sig") as f:
    content = f.read()

# Remove the bonding flag check block
old_block = """    if (bond_collapse_positions or bonding_strict) and not allow_bonding:
        raise NaturalMathValidationError(
            "Section 17 bonding flags: collapse/strict require allow_bonding"
        )
"""
content = content.replace(old_block, "")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("core_step.py: removed bonding flag check")

# ============================================================
# ISSUE 4: Fix cluster_step.py - ValueError to NaturalMathValidationError
# ============================================================
path = r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION\natural_math_v5\cluster_step.py"
with open(path, "r", encoding="utf-8-sig") as f:
    content = f.read()

# Add import for NaturalMathValidationError
old_import = "from .cluster_actions import ("
new_import = "from .errors import NaturalMathValidationError\nfrom .cluster_actions import ("
content = content.replace(old_import, new_import, 1)

# Replace all ValueError with NaturalMathValidationError in check_cluster_invariants
content = content.replace(
    'raise ValueError("duplicate cluster node id")',
    'raise NaturalMathValidationError("Section 6A cluster: duplicate cluster node id")'
)
content = content.replace(
    'raise ValueError("bond points to absent id")',
    'raise NaturalMathValidationError("Section 6A cluster: bond points to absent id")'
)
content = content.replace(
    'raise ValueError("live bond is not symmetric")',
    'raise NaturalMathValidationError("Section 6A cluster: live bond is not symmetric")'
)
content = content.replace(
    'raise ValueError("live node exceeds max live bonds")',
    'raise NaturalMathValidationError("Section 6A cluster: live node exceeds max live bonds")'
)
content = content.replace(
    'raise ValueError("live node below tau")',
    'raise NaturalMathValidationError("Section 6A cluster: live node below tau")'
)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("cluster_step.py: ValueError -> NaturalMathValidationError")

# ============================================================
# ISSUE 5: Rewrite sample_two in randomness.py
# ============================================================
path = r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION\natural_math_v5\randomness.py"
with open(path, "r", encoding="utf-8-sig") as f:
    content = f.read()

old_sample_two = """def sample_two(rng: TraceRng, items: list[Any]) -> tuple[Any, Any]:
    \"\"\"Section 8: random unordered pair without replacement.\"\"\"
    result = rng.sample(items, 2)
    return result[0], result[1]"""

new_sample_two = """def sample_two(rng: TraceRng, seq: list[Any]) -> tuple[Any, Any]:
    \"\"\"Section 8: random unordered pair without replacement.

    Algorithm (per spec):
    1. randrange(0, len(seq)) to pick first index
    2. Remove that index from sequence (preserving order)
    3. randrange(0, len(remaining)) to pick second index
    4. Return (seq[idx1], remaining[idx2])

    Does NOT use rng.sample().
    \"\"\"
    if len(seq) < 2:
        raise ValueError("sample_two requires at least 2 items")
    i = rng.randrange(0, len(seq))
    first = seq[i]
    remaining = seq[:i] + seq[i + 1:]
    j = rng.randrange(0, len(remaining))
    second = remaining[j]
    return first, second"""

content = content.replace(old_sample_two, new_sample_two)

# Also remove the sample method from TraceRng since it's no longer needed
old_sample_method = """
    def sample(self, population: list[Any], k: int) -> list[Any]:
        return self.inner.sample(population, k)"""
content = content.replace(old_sample_method, "")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("randomness.py: sample_two rewritten per spec algorithm")

# ============================================================
# ISSUE 6: Strict tuple validation in validation.py
# ============================================================
path = r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION\natural_math_v5\validation.py"
with open(path, "r", encoding="utf-8-sig") as f:
    content = f.read()

# Add as_tuple3_strict function
old_as_tuple3 = """def as_tuple3(value: Any, field_name: str) -> tuple[int, int, int]:
    \"\"\"Validate a 3-integer tuple. Section 6.\"\"\"
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise NaturalMathValidationError(
            f"Section 6 {field_name}: must be 3-integer tuple"
        )
    result = tuple(value)
    if any(type(v) is not int for v in result):
        raise NaturalMathValidationError(
            f"Section 6 {field_name}: must be 3-integer tuple"
        )
    return result  # type: ignore[return-value]"""

new_as_tuple3 = """def as_tuple3(value: Any, field_name: str) -> tuple[int, int, int]:
    \"\"\"Validate a 3-integer tuple. Section 6.

    Accepts both lists and tuples for backward compatibility with
    test helpers that convert JSON fixtures before calling run_step.
    \"\"\"
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise NaturalMathValidationError(
            f"Section 6 {field_name}: must be 3-integer tuple"
        )
    result = tuple(value)
    if any(type(v) is not int for v in result):
        raise NaturalMathValidationError(
            f"Section 6 {field_name}: must be 3-integer tuple"
        )
    return result  # type: ignore[return-value]


def as_tuple3_strict(value: Any, field_name: str) -> tuple[int, int, int]:
    \"\"\"Validate a 3-integer tuple. Section 6. Rejects lists.

    The model requires tuples for pos and direction. JSON fixture
    deserialization must convert lists to tuples BEFORE calling run_step.
    This is a test helper responsibility, not model responsibility.
    \"\"\"
    if not isinstance(value, tuple) or len(value) != 3:
        raise NaturalMathValidationError(
            f"Section 6 {field_name}: must be 3-integer tuple (got {type(value).__name__})"
        )
    if any(type(v) is not int for v in value):
        raise NaturalMathValidationError(
            f"Section 6 {field_name}: all elements must be int"
        )
    return value"""

content = content.replace(old_as_tuple3, new_as_tuple3)

# Change validate_nodes to use as_tuple3_strict for pos and direction
content = content.replace(
    'node["pos"] = as_tuple3(node["pos"], "pos")',
    'node["pos"] = as_tuple3_strict(node["pos"], "pos")'
)
content = content.replace(
    'node["direction"] = as_tuple3(node["direction"], "direction")',
    'node["direction"] = as_tuple3_strict(node["direction"], "direction")'
)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("validation.py: added as_tuple3_strict, validate_nodes uses strict checks")
print("ALL batch 1 fixes applied")
