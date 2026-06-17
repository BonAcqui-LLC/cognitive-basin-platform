"""Compatibility entrypoint for ``python -m basinlab.cli.main``."""

from python.basinlab.cli.main import main


if __name__ == "__main__":
    raise SystemExit(main())
