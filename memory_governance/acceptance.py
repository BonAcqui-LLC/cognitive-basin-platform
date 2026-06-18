"""
Compatibility wrapper for memory_governance acceptance entrypoint.
"""

from python.memory_governance.acceptance import main


if __name__ == "__main__":
    raise SystemExit(main())
