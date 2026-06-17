"""Compatibility entrypoint for ``python -m basinlab.acceptance``."""

from python.basinlab.acceptance import main


if __name__ == "__main__":
    raise SystemExit(main())
