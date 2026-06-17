"""
Compatibility wrapper for evaluation_lab acceptance entrypoint.
"""

from python.evaluation_lab.acceptance import main


if __name__ == "__main__":
    raise SystemExit(main())
