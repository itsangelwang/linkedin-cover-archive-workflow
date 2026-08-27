#!/usr/bin/env python3
"""Create a collision-safe archive folder for one LinkedIn article."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import unicodedata
from datetime import date
from pathlib import Path


MAX_SOURCE_BYTES = 100 * 1024 * 1024
MAX_SLUG_LENGTH = 80


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
    slug = slug[:MAX_SLUG_LENGTH].rstrip("-")
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
    try:
        size = path.stat().st_size
    except OSError as error:
        raise SystemExit("unable to inspect an article source file") from error
    if size > MAX_SOURCE_BYTES:
        raise SystemExit(f"article source must not exceed {MAX_SOURCE_BYTES} bytes")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_existing_archive(root: Path, source_hash: str) -> Path | None:
    if not root.exists():
        return None
    for article_dir in sorted(
        path for path in root.iterdir() if path.is_dir() and not path.is_symlink()
    ):
        source_dir = article_dir / "source"
        if source_dir.is_symlink() or not source_dir.is_dir():
            continue
        for candidate in sorted(
            path for path in source_dir.iterdir() if path.is_file() and not path.is_symlink()
        ):
            if sha256(candidate) == source_hash:
                return article_dir
    return None


def has_git_marker(start: Path) -> bool:
    current = start.resolve()
    return any((directory / ".git").exists() for directory in (current, *current.parents))


def safe_project_path(raw_path: Path, label: str, include_leaf: bool = True) -> Path:
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


def display_project_path(path: Path) -> str:
    return path.relative_to(Path.cwd().resolve()).as_posix()


def git_executable() -> str:
    candidates = ("/usr/bin/git", shutil.which("git"))
    for candidate in candidates:
        if not candidate:
            continue
        executable = Path(candidate).resolve()
        if executable.is_file() and os.access(executable, os.X_OK):
            return str(executable)
    raise SystemExit("Git is unavailable; cannot verify archive privacy")


def run_git(*args: str, allowed_returncodes: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            [git_executable(), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
    except FileNotFoundError as error:
        raise SystemExit("Git is unavailable; cannot verify archive privacy") from error
    except subprocess.TimeoutExpired as error:
        raise SystemExit("Git timed out while verifying archive privacy") from error
    if result.returncode not in allowed_returncodes:
        raise SystemExit("Git failed while verifying archive privacy")
    return result


def protect_archive_from_git(root: Path) -> None:
    """Keep a repository-local archive out of normal Git staging."""
    try:
        inside_result = run_git("rev-parse", "--is-inside-work-tree")
    except SystemExit:
        if not has_git_marker(Path.cwd()):
            return
        raise
    if inside_result.stdout.strip() != "true":
        return

    repository_text = run_git("rev-parse", "--show-toplevel").stdout.strip()
    if not repository_text:
        raise SystemExit("Git returned an empty repository root")
    repository = Path(repository_text).resolve()
    archive = root.resolve()
    try:
        relative = archive.relative_to(repository)
    except ValueError:
        return
    if relative == Path("."):
        raise SystemExit("archive root cannot be the Git repository root")
    if any(character in relative.as_posix() for character in "\n\r*?[\\"):
        raise SystemExit("archive root contains characters unsafe for a Git exclude pattern")

    tracked_text = run_git("ls-files", "--", relative.as_posix()).stdout.strip()
    tracked = [
        item
        for item in tracked_text.splitlines()
        if item and Path(item).name != ".gitkeep"
    ]
    if tracked:
        raise SystemExit(
            "archive root already contains Git-tracked files; untrack and review them "
            "before storing private article data"
        )

    exclude_text = run_git("rev-parse", "--git-path", "info/exclude").stdout.strip()
    if not exclude_text:
        raise SystemExit("unable to locate Git's local exclude file")
    exclude = Path(exclude_text)
    if not exclude.is_absolute():
        exclude = Path.cwd() / exclude
    if exclude.is_symlink():
        raise SystemExit("Git's local exclude file must not be a symbolic link")
    exclude.parent.mkdir(parents=True, exist_ok=True)

    pattern = f"/{relative.as_posix().rstrip('/')}/**"
    existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    if pattern not in existing.splitlines():
        prefix = "" if not existing or existing.endswith("\n") else "\n"
        flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(exclude, flags, 0o600)
        with os.fdopen(descriptor, "a", encoding="utf-8") as stream:
            stream.write(f"{prefix}# Private article archives created by linkedin-cover-archive-workflow\n")
            stream.write(f"{pattern}\n")

    probe = archive / ".privacy-check"
    ignored = run_git(
        "check-ignore", "--no-index", "--", str(probe), allowed_returncodes=(0, 1)
    )
    if ignored.returncode != 0:
        raise SystemExit("failed to verify that the archive root is ignored by Git")


def main() -> int:
    args = parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        raise SystemExit("--date must use YYYY-MM-DD")

    args.root = safe_project_path(args.root, "archive root")
    protect_archive_from_git(args.root)

    source = args.source.expanduser().resolve() if args.source else None
    source_hash = None
    if source:
        if not source.is_file():
            raise SystemExit(f"--source is not a file: {args.source}")
        source_hash = sha256(source)
        existing = find_existing_archive(args.root, source_hash)
        if existing:
            print(display_project_path(existing))
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

    print(display_project_path(target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
