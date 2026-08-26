#!/usr/bin/env python3
"""Validate LinkedIn cover ratio and create a non-cropped mobile preview."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from PIL import Image


TARGET_RATIO = 1.91
DEFAULT_TOLERANCE = 0.03
MAX_INPUT_PIXELS = 50_000_000
MAX_PREVIEW_WIDTH = 10_000


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
    if args.width > MAX_PREVIEW_WIDTH:
        raise SystemExit(f"--width must not exceed {MAX_PREVIEW_WIDTH}")
    if not 0 <= args.tolerance <= 1:
        raise SystemExit("--tolerance must be between 0 and 1")

    input_path = args.input.expanduser().resolve()
    output = (
        args.output.expanduser().resolve()
        if args.output
        else input_path.with_name(f"{input_path.stem}-mobile.jpg")
    )
    if input_path == output:
        raise SystemExit("output must not overwrite the input image")

    with Image.open(input_path) as source:
        width, height = source.size
        if width <= 0 or height <= 0 or width * height > MAX_INPUT_PIXELS:
            raise SystemExit(f"input image must not exceed {MAX_INPUT_PIXELS} pixels")
        image = source.convert("RGB")
        ratio = width / height
        output.parent.mkdir(parents=True, exist_ok=True)
        preview_height = max(1, round(args.width / ratio))
        preview = image.resize((args.width, preview_height), Image.Resampling.LANCZOS)
        temporary_name = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=output.parent, prefix=f".{output.name}.", suffix=".tmp", delete=False
            ) as temporary:
                temporary_name = temporary.name
            preview.save(temporary_name, "JPEG", quality=90, optimize=True)
            os.replace(temporary_name, output)
            temporary_name = None
        finally:
            if temporary_name:
                Path(temporary_name).unlink(missing_ok=True)

    delta = abs(ratio - TARGET_RATIO)
    status = "PASS" if delta <= args.tolerance else "WARN"
    print(
        f"{status}: {width}x{height}, ratio={ratio:.4f}, "
        f"target={TARGET_RATIO:.2f}, preview={output}"
    )
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
