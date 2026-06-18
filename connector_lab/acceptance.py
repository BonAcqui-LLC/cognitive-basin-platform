"""
Compatibility wrapper for connector_lab acceptance entrypoint.
"""

from python.connector_lab.acceptance import main


if __name__ == "__main__":
    raise SystemExit(main())
