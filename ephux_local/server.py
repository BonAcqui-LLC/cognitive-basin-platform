"""Compatibility entrypoint for ``python -m ephux_local.server``."""

from python.ephux_local.service import main


if __name__ == "__main__":
    raise SystemExit(main())
