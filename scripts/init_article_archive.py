#!/usr/bin/env python3
"""Create a collision-safe archive folder for one LinkedIn article."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import unicodedata
from datetime import date
from pathlib import Path


TEMPLATES = {
    "brief.md": """# Article brief

## Thesis

## Strongest conflict, discovery, or conclusion

## Audience

## Evidence limits

## Cover focus

## Claims not to exaggerate
""",
    "strategy.md": """# Article content and cover visual analysis

## 1. Article core

## 2. Cover communication goal

## 3. Title recommendations

## 4. Three distinct visual directions

### Direction 1

### Direction 2

### Direction 3

## 5. Recommended direction

## 6. Generation restrictions
""",
    "prompts.md": """# Approved generation prompts

## Direction 1

## Direction 2

## Direction 3

## Shared restrictions

- Horizontal 1.91:1 composition.
- No generated text or logos.
- Preserve 35–40% quiet headline-safe space.
""",
    "decision.md": """# Final decision

## Selected candidate

## Why it won

## Why alternatives were rejected

## Revision history

## Final delivery

- Final filename:
- Recommended title:
- Line breaks:
- Placement:
- Approximate title width:

## Proposed reusable lesson

Pending user confirmation.
""",
}


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return slug or "article"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("title", help="Article title used for the archive slug")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--slug", help="Override the generated ASCII slug")
    parser.add_argument("--root", type=Path, default=Path("articles"))
    parser.add_argument("--source", type=Path, help="Original article file to deduplicate and preserve")
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_existing_archive(root: Path, source_hash: str) -> Path | None:
    if not root.exists():
        return None
    for article_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        source_dir = article_dir / "source"
        if not source_dir.is_dir():
            continue
        for candidate in sorted(path for path in source_dir.iterdir() if path.is_file()):
            if sha256(candidate) == source_hash:
                return article_dir
    return None


def main() -> int:
    args = parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        raise SystemExit("--date must use YYYY-MM-DD")

    source = args.source.expanduser().resolve() if args.source else None
    source_hash = None
    if source:
        if not source.is_file():
            raise SystemExit(f"--source is not a file: {source}")
        source_hash = sha256(source)
        existing = find_existing_archive(args.root, source_hash)
        if existing:
            print(existing)
            return 0

    slug = slugify(args.slug or args.title)
    base = args.root / f"{args.date}-{slug}"
    target = base
    suffix = 2
    while target.exists():
        target = Path(f"{base}-{suffix}")
        suffix += 1

    for folder in ("source", "candidates", "previews", "final"):
        (target / folder).mkdir(parents=True, exist_ok=True)
    for filename, content in TEMPLATES.items():
        (target / filename).write_text(content, encoding="utf-8")

    if source and source_hash:
        preserved = target / "source" / source.name
        shutil.copy2(source, preserved)
        if sha256(preserved) != source_hash:
            raise SystemExit("source copy verification failed")

    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
