#!/usr/bin/env python3
"""
Path-aware, policy-driven placeholder scanner for Cognitive Basin platform.
Fail-closed. Uses only git-tracked files.
Release scope filtering via policy include/exclude.
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

def should_scan(path: str, include_paths: list, exclude_paths: list) -> bool:
    for ex in exclude_paths:
        if fnmatch(path, ex):
            return False
    for inc in include_paths:
        if fnmatch(path, inc):
            return True
    return False

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
    # Programmatic to avoid full literals in this source
    prohibited = [
        "PLACE" + "HOLDER",
        "INSERT " + "CODE",
        "ADD " + "CODE HERE",
        "FULL " + "CODE HERE",
        "IMPLEMENT " + "LATER",
        "MOCK " + "SUCCESS",
        "SIMULATED " + "SUCCESS",
        "TO" + "DO",
        "TB" + "D"
    ]
    authorized = policy.get("authorized", {})
    include_paths = policy.get("include_paths", ["**/*"])
    exclude_paths = policy.get("exclude_paths", ["evidence/**", "ops/verification/**"])

    files = get_tracked_files()
    unauthorized = []
    authorized_matches = []

    for f in files:
        if not should_scan(f, include_paths, exclude_paths):
            continue
        try:
            content = Path(f).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            print(f"FAIL: unreadable file {f}")
            sys.exit(1)
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