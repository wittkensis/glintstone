#!/usr/bin/env python3
"""
add-headers.py — retrofit and validate YAML frontmatter on Glintstone docs.

Owned by gs-curator-docs. Schema lives in header-schema.md.

Usage:
    python add-headers.py --check          # exit 1 if any file is missing/invalid
    python add-headers.py --check --paths data-model docs   # check subset
    python add-headers.py                  # write stub headers to files missing one
    python add-headers.py --dry-run        # show what would change

Skips:
    - source-data/sources/**     (vendored upstream)
    - venv/, node_modules/, .venv/, .git/, .mypy_cache/, .pytest_cache/, .ruff_cache/
    - _archive/                  (about to be deleted)
    - any file containing "auto-generated" in first 5 lines
    - PLAN/PRIVATE-TODO.md       (user-owned)
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[3]
TODAY = dt.date.today().isoformat()

SKIP_DIR_PARTS = {
    "venv",
    ".venv",
    "node_modules",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "_archive",
    "__pycache__",
}

SKIP_PATH_PREFIXES = ("source-data/sources/",)

SKIP_FILES = {
    "PLAN/PRIVATE-TODO.md",
    "README.md",  # GitHub repo landing page — YAML frontmatter renders awkwardly there
    "CLAUDE.md",  # loaded verbatim by Claude every session; no frontmatter
}

REQUIRED_FIELDS = [
    "question",
    "created",
    "modified",
    "context",
    "status",
    "audience",
    "owners",
]
OPTIONAL_FIELDS = ["related_issues", "related_skills", "supersedes", "superseded_by"]
SKILL_TOP_LEVEL = [
    "name",
    "description",
]  # required at top level for SKILL.md (VS Code-compatible)
SKILL_METADATA_EXTRA = ["triggers"]  # required under `metadata:` for SKILL.md

VALID_STATUS = {"active", "draft", "archived", "deprecated"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIR_PARTS:
        return True
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel in SKIP_FILES:
        return True
    for prefix in SKIP_PATH_PREFIXES:
        if rel.startswith(prefix):
            return True
    try:
        first_lines = "\n".join(path.read_text(errors="replace").splitlines()[:5])
    except OSError:
        return True
    if "auto-generated" in first_lines.lower():
        return True
    return False


def iter_markdown(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if root.is_file() and root.suffix == ".md":
            if not should_skip(root):
                yield root
            continue
        for path in root.rglob("*.md"):
            if not should_skip(path):
                yield path


def has_header(text: str) -> bool:
    return text.startswith("---\n")


def parse_header(text: str) -> dict | None:
    """Tiny YAML-ish parser. Doesn't pull in PyYAML.

    Returns a single flat dict. For SKILL.md files using the VS Code-compatible
    shape (top-level `name` + `description` + `metadata:` block with our custom
    fields), the nested `metadata:` block is flattened into the same dict so
    validation can find all expected keys regardless of where they live.
    """
    if not has_header(text):
        return None
    try:
        end = text.index("\n---", 4)
    except ValueError:
        return None
    body = text[4:end]
    fields: dict[str, str] = {}
    in_metadata = False
    for line in body.splitlines():
        if not line:
            in_metadata = False
            continue
        if line.startswith("  ") and in_metadata:
            stripped = line.strip()
            if ":" not in stripped:
                continue
            key, _, value = stripped.partition(":")
            fields[key.strip()] = value.strip()
            continue
        if line.startswith(" "):
            continue
        if ":" not in line:
            in_metadata = False
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if key == "metadata":
            in_metadata = True
            continue
        in_metadata = False
        fields[key] = value
    return fields


def validate(path: Path, fields: dict, is_skill: bool) -> list[str]:
    errors: list[str] = []
    for f in REQUIRED_FIELDS:
        if f not in fields:
            errors.append(f"missing required field: {f}")
    if is_skill:
        for f in SKILL_TOP_LEVEL:
            if f not in fields:
                errors.append(f"missing skill top-level field: {f}")
        for f in SKILL_METADATA_EXTRA:
            if f not in fields:
                errors.append(f"missing skill metadata field: {f}")
    if "created" in fields and not DATE_RE.match(fields["created"]):
        errors.append(f"invalid created date: {fields['created']!r} (want YYYY-MM-DD)")
    if "modified" in fields and not DATE_RE.match(fields["modified"]):
        errors.append(
            f"invalid modified date: {fields['modified']!r} (want YYYY-MM-DD)"
        )
    if "status" in fields and fields["status"] not in VALID_STATUS:
        errors.append(
            f"invalid status: {fields['status']!r} (allowed: {sorted(VALID_STATUS)})"
        )
    if "audience" in fields and fields["audience"] in ("[]", ""):
        errors.append("audience must be non-empty")
    return errors


def stub_header(path: Path, is_skill: bool) -> str:
    if is_skill:
        name = path.parent.name
        return f"""---
name: {name}
description: "TODO: one sentence — what does this skill do?"
metadata:
  question: "TODO: one sentence — what question does this skill answer?"
  created: {TODAY}
  modified: {TODAY}
  context: "TODO: why was this skill created?"
  status: draft
  audience: [engineers, claude]
  owners: [eric]
  related_issues: []
  related_skills: []
  supersedes: null
  superseded_by: null
  triggers: []
---

"""
    return f"""---
question: "TODO: one sentence — what question does {path.name} answer?"
created: {TODAY}
modified: {TODAY}
context: "TODO: why was this file created?"
status: draft
audience: [engineers]
owners: [eric]
related_issues: []
related_skills: []
supersedes: null
superseded_by: null
---

"""


def is_skill_file(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT).as_posix()
    return rel.startswith(".claude/skills/") and path.name == "SKILL.md"


def cmd_check(roots: list[Path]) -> int:
    bad = 0
    for path in iter_markdown(roots):
        text = path.read_text(errors="replace")
        rel = path.relative_to(REPO_ROOT).as_posix()
        if not has_header(text):
            print(f"MISSING HEADER  {rel}")
            bad += 1
            continue
        fields = parse_header(text)
        if fields is None:
            print(f"UNCLOSED HEADER  {rel}")
            bad += 1
            continue
        errors = validate(path, fields, is_skill_file(path))
        if errors:
            print(f"INVALID HEADER  {rel}")
            for e in errors:
                print(f"  - {e}")
            bad += 1
    if bad:
        print(f"\n{bad} file(s) need attention.")
        return 1
    print("All checked files have valid headers.")
    return 0


def cmd_add(roots: list[Path], dry_run: bool) -> int:
    added = 0
    for path in iter_markdown(roots):
        text = path.read_text(errors="replace")
        if has_header(text):
            continue
        header = stub_header(path, is_skill_file(path))
        rel = path.relative_to(REPO_ROOT).as_posix()
        if dry_run:
            print(f"would add header to  {rel}")
        else:
            path.write_text(header + text)
            print(f"added stub header to  {rel}")
        added += 1
    if added == 0:
        print("Every file already has a header.")
    elif dry_run:
        print(f"\n{added} file(s) would get a stub header.")
    else:
        print(f"\n{added} stub header(s) added. Fill in the TODOs.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--check",
        action="store_true",
        help="validate headers; exit 1 if any are missing/invalid",
    )
    p.add_argument(
        "--dry-run", action="store_true", help="show what would change, don't write"
    )
    p.add_argument(
        "--paths", nargs="*", default=None, help="paths to scan (default: repo root)"
    )
    args = p.parse_args()

    if args.paths:
        roots = [Path(p).resolve() for p in args.paths]
    else:
        roots = [REPO_ROOT]

    if args.check:
        return cmd_check(roots)
    return cmd_add(roots, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
