from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish import compare_images, ensure_reference_library_scaffold


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare two images with the Fractalish Translation Apparatus v0.1.")
    parser.add_argument("left", help="Left image path.")
    parser.add_argument("right", help="Right image path.")
    parser.add_argument("--out", required=True, help="Output directory for comparison artifacts.")
    args = parser.parse_args(argv)

    ensure_reference_library_scaffold()
    compare_images(Path(args.left), Path(args.right), Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
