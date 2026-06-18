"""
Compatibility wrapper for action_permit acceptance entrypoint.
"""

from python.action_permit.acceptance import main


if __name__ == "__main__":
    raise SystemExit(main())
