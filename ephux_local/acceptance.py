"""Compatibility entrypoint for ``python -m ephux_local.acceptance``."""

from python.ephux_local.acceptance import main


if __name__ == "__main__":
    raise SystemExit(main())
