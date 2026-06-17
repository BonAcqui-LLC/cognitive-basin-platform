"""
Compatibility wrapper for sandbox_lab acceptance entrypoint.
"""

from python.sandbox_lab.acceptance import main


if __name__ == "__main__":
    raise SystemExit(main())
