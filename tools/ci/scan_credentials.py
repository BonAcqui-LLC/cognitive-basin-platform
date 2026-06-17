#!/usr/bin/env python3
import json, re, subprocess, sys
from pathlib import Path
from fnmatch import fnmatch

def main():
    ppath = Path("ops/policies/credential-scan-policy.json")
    if ppath.exists():
        pol = json.loads(ppath.read_text())
        prohibited = pol.get("prohibited", [])
    else:
        prohibited = ["gho_[A-Za-z0-9_-]+", "sk-[A-Za-z0-9_-]+", "xai-[A-Za-z0-9_-]+", "ALL_TOKENS_KEYS_FOR_GROK"]
    files = subprocess.check_output(["git","ls-files"], text=True).splitlines()
    bad = []
    for f in files:
        if not any(f.endswith(e) for e in (".py",".js",".ts",".json",".toml",".md",".txt",".yml")): continue
        try:
            c = Path(f).read_text(errors="ignore")
        except: continue
        for pat in prohibited:
            if re.search(pat, c):
                bad.append((f, pat))
    for f,p in bad:
        print(f"CREDENTIAL: {f} matches {p}")
    if bad:
        print("Credential scan: FAILED")
        sys.exit(1)
    print("Credential scan: PASS")
    sys.exit(0)
if __name__=="__main__": main()
