"""
Compatibility wrapper for provider_lab acceptance entrypoint.
"""

from python.provider_lab.acceptance import main


if __name__ == "__main__":
    raise SystemExit(main())
