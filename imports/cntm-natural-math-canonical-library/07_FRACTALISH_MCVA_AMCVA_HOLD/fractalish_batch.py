from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish import batch_analyze_folder, ensure_reference_library_scaffold


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Batch-analyze a folder with the Fractalish Translation Apparatus v0.1.")
    parser.add_argument("input_dir", help="Folder containing input images.")
    parser.add_argument("--out", required=True, help="Output directory for batch artifacts.")
    args = parser.parse_args(argv)

    ensure_reference_library_scaffold()
    batch_analyze_folder(Path(args.input_dir), Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
