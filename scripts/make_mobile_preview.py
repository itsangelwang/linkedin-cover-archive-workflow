#!/usr/bin/env python3
"""Validate LinkedIn cover ratio and create a non-cropped mobile preview."""

from __future__ import annotations

import argparse
import os
import secrets
import stat
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError


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
    parser.add_argument("--force", action="store_true", help="Replace an existing regular output file")
    return parser.parse_args()


def safe_workspace_path(raw_path: Path, label: str, include_leaf: bool) -> Path:
    workspace = Path.cwd().resolve()
    lexical = Path(os.path.abspath(raw_path.expanduser()))
    try:
        relative = lexical.relative_to(workspace)
    except ValueError as error:
        raise SystemExit(f"{label} must stay inside the current working directory") from error

    cursor = workspace
    parts = relative.parts if include_leaf else relative.parts[:-1]
    for part in parts:
        cursor /= part
        if cursor.is_symlink():
            raise SystemExit(f"{label} path must not contain symbolic links")
    return lexical


def save_jpeg_safely(image: Image.Image, output: Path, parent: Path, force: bool) -> None:
    directory_flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        directory_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    directory_descriptor = os.open(parent, directory_flags)
    temporary_name = f".{output.name}.{secrets.token_hex(8)}.tmp"
    try:
        try:
            existing = os.stat(output.name, dir_fd=directory_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            existing = None
        if existing is not None:
            if stat.S_ISLNK(existing.st_mode):
                raise SystemExit("output must not be a symbolic link")
            if not stat.S_ISREG(existing.st_mode):
                raise SystemExit("output must be a regular file")
            if not force:
                raise SystemExit("output already exists; use --force to replace it")

        descriptor = os.open(
            temporary_name,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
            dir_fd=directory_descriptor,
        )
        try:
            with os.fdopen(descriptor, "wb") as stream:
                image.save(stream, "JPEG", quality=90, optimize=True)
        except BaseException:
            os.unlink(temporary_name, dir_fd=directory_descriptor)
            raise
        os.replace(
            temporary_name,
            output.name,
            src_dir_fd=directory_descriptor,
            dst_dir_fd=directory_descriptor,
        )
    finally:
        try:
            os.unlink(temporary_name, dir_fd=directory_descriptor)
        except FileNotFoundError:
            pass
        os.close(directory_descriptor)


def main() -> int:
    args = parse_args()
    if args.width <= 0:
        raise SystemExit("--width must be positive")
    if args.width > MAX_PREVIEW_WIDTH:
        raise SystemExit(f"--width must not exceed {MAX_PREVIEW_WIDTH}")
    if not 0 <= args.tolerance <= 1:
        raise SystemExit("--tolerance must be between 0 and 1")

    input_path = safe_workspace_path(args.input, "input", include_leaf=True)
    if not input_path.is_file():
        raise SystemExit(f"input is not a file: {args.input}")
    raw_output = args.output or args.input.with_name(f"{args.input.stem}-mobile.jpg")
    output = safe_workspace_path(raw_output, "output", include_leaf=False)
    if output.exists() and os.path.samefile(input_path, output):
        raise SystemExit("output must not overwrite the input image")

    try:
        with Image.open(input_path) as source:
            width, height = source.size
            if width <= 0 or height <= 0 or width * height > MAX_INPUT_PIXELS:
                raise SystemExit(f"input image must not exceed {MAX_INPUT_PIXELS} pixels")
            image = source.convert("RGB")
            ratio = width / height
            output.parent.mkdir(parents=True, exist_ok=True)
            output_parent = output.parent.resolve(strict=True)
            preview_height = max(1, round(args.width / ratio))
            preview = image.resize((args.width, preview_height), Image.Resampling.LANCZOS)
            save_jpeg_safely(preview, output, output_parent, args.force)
    except UnidentifiedImageError:
        raise SystemExit("input is not a supported image") from None
    except OSError:
        raise SystemExit("image processing failed without writing the output") from None

    delta = abs(ratio - TARGET_RATIO)
    status = "PASS" if delta <= args.tolerance else "WARN"
    display_output = output.relative_to(Path.cwd().resolve()).as_posix()
    print(
        f"{status}: {width}x{height}, ratio={ratio:.4f}, "
        f"target={TARGET_RATIO:.2f}, preview={display_output}"
    )
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
