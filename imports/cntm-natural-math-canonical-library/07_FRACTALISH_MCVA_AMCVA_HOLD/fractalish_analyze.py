from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish import analyze_image, ensure_reference_library_scaffold


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze one image with the Fractalish Translation Apparatus v0.1.")
    parser.add_argument("image", help="Input image path.")
    parser.add_argument("--out", required=True, help="Output directory for the case package.")
    parser.add_argument("--title", default="", help="Optional case title.")
    parser.add_argument("--domain", default="unknown", help="Optional domain label.")
    parser.add_argument("--subdomain", default="unknown", help="Optional subdomain label.")
    parser.add_argument("--source", default="", help="Optional source note or dataset label.")
    parser.add_argument("--family-hint", default="", help="Optional morphology-family hint.")
    args = parser.parse_args(argv)

    ensure_reference_library_scaffold()
    analyze_image(
        Path(args.image),
        Path(args.out),
        title=args.title or None,
        domain=args.domain,
        subdomain=args.subdomain,
        source=args.source,
        family_hint=args.family_hint,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
