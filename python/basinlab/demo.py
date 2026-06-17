"""
Executable BasinLab vertical-slice demonstration.

Run:
    python -m python.basinlab.demo
"""

from __future__ import annotations

import json

from .session import run_vertical_slice_demo


def main() -> int:
    result = run_vertical_slice_demo()
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
