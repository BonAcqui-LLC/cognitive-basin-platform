#!/usr/bin/env python3
"""
Path-aware, policy-driven placeholder scanner for Cognitive Basin platform.
Fail-closed. Uses only git-tracked files.
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from fnmatch import fnmatch

def load_policy(path: Path):
    if not path.exists():
        print(f"FAIL: policy file missing: {path}")
        sys.exit(1)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FAIL: malformed policy: {e}")
        sys.exit(1)

def get_tracked_files():
    try:
        out = subprocess.check_output(
            ["git", "ls-files"], text=True, cwd=".", stderr=subprocess.DEVNULL
        )
        return [f for f in out.splitlines() if f.strip()]
    except Exception as e:
        print(f"FAIL: could not get git ls-files: {e}")
        sys.exit(1)

def matches_authorized(path: str, line: str, pattern: str, authorized: dict) -> bool:
    auth_list = authorized.get(pattern, [])
    for auth in auth_list:
        if ":" in auth:
            auth_path, auth_ctx = auth.split(":", 1)
            if fnmatch(path, auth_path) and auth_ctx in line:
                return True
        else:
            if fnmatch(path, auth):
                return True
    return False

def main():
    policy_path = Path("ops/policies/placeholder-scan-policy.json")
    policy = load_policy(policy_path)
    prohibited = policy.get("prohibited", [])
    authorized = policy.get("authorized", {})
    rules = policy.get("rules", {})

    files = get_tracked_files()
    unauthorized = []
    authorized_matches = []

    source_exts = (".py", ".js", ".ts", ".json", ".toml", ".md", ".txt", ".yml", ".yaml")

    for f in files:
        if not f.endswith(source_exts):
            continue
        try:
            content = Path(f).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for lineno, line in enumerate(content.splitlines(), 1):
            for pat in prohibited:
                if re.search(re.escape(pat), line, re.IGNORECASE):
                    is_auth = matches_authorized(f, line, pat, authorized)
                    if is_auth:
                        authorized_matches.append((f, lineno, pat))
                    else:
                        unauthorized.append((f, lineno, pat, line.strip()[:120]))

    for f, ln, pat in authorized_matches:
        print(f"AUTHORIZED: {f}:{ln}: {pat}")

    if unauthorized:
        print("\nUNAUTHORIZED MATCHES (failing scan):")
        for f, ln, pat, snippet in unauthorized:
            print(f"  {f}:{ln}: {pat} in: {snippet}")
        print(f"\nPlaceholder scan: FAILED ({len(unauthorized)} unauthorized)")
        sys.exit(1)

    print("Placeholder scan: PASS (only authorized matches or clean)")
    sys.exit(0)

if __name__ == "__main__":
    main()