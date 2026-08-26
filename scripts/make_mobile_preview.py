#!/usr/bin/env python3
"""Validate LinkedIn cover ratio and create a non-cropped mobile preview."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image


TARGET_RATIO = 1.91
DEFAULT_TOLERANCE = 0.03


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--width", type=int, default=360)
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.width <= 0:
        raise SystemExit("--width must be positive")
    if args.tolerance < 0:
        raise SystemExit("--tolerance must be non-negative")

    with Image.open(args.input) as source:
        image = source.convert("RGB")
        width, height = image.size
        ratio = width / height
        output = args.output or args.input.with_name(f"{args.input.stem}-mobile.jpg")
        output.parent.mkdir(parents=True, exist_ok=True)
        preview_height = max(1, round(args.width / ratio))
        preview = image.resize((args.width, preview_height), Image.Resampling.LANCZOS)
        preview.save(output, "JPEG", quality=90, optimize=True)

    delta = abs(ratio - TARGET_RATIO)
    status = "PASS" if delta <= args.tolerance else "WARN"
    print(
        f"{status}: {width}x{height}, ratio={ratio:.4f}, "
        f"target={TARGET_RATIO:.2f}, preview={output}"
    )
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
