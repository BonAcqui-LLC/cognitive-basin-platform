#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path


SCANNED_SUFFIXES = (".py", ".js", ".ts", ".json", ".toml", ".md", ".txt", ".yml")
SELF_EXCLUDES = {"tools/ci/scan_credentials.py", "ops/policies/credential-scan-policy.json"}


def scan_files(
    files: list[str],
    prohibited: list[str],
    prohibited_paths: list[str],
    *,
    root: Path = Path("."),
) -> list[tuple[str, str, str]]:
    bad: list[tuple[str, str, str]] = []
    for file_name in files:
        for pattern in prohibited_paths:
            if re.search(pattern, file_name, re.IGNORECASE):
                bad.append((file_name, "path", pattern))
        if not file_name.endswith(SCANNED_SUFFIXES) or file_name in SELF_EXCLUDES:
            continue
        try:
            content = (root / file_name).read_text(errors="ignore")
        except OSError:
            continue
        for pattern in prohibited:
            if re.search(pattern, content):
                bad.append((file_name, "content", pattern))
    return bad


def main():
    policy_path = Path("ops/policies/credential-scan-policy.json")
    if policy_path.exists():
        policy = json.loads(policy_path.read_text())
        prohibited = policy.get("prohibited", [])
        prohibited_paths = policy.get("prohibited_paths", [])
    else:
        prohibited = [
            "gho_[A-Za-z0-9_-]{20,}",
            "sk-[A-Za-z0-9_-]{20,}",
            "xai-[A-Za-z0-9_-]{20,}",
        ]
        prohibited_paths = ["ALL_TOKENS_KEYS_FOR_GROK"]
    files = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
    bad = scan_files(files, prohibited, prohibited_paths)
    for file_name, match_kind, pattern in bad:
        print(f"CREDENTIAL: {file_name} {match_kind} matches {pattern}")
    if bad:
        print("Credential scan: FAILED")
        sys.exit(1)
    print("Credential scan: PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
