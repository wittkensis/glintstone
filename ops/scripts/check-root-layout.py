#!/usr/bin/env python3
"""Pre-commit guard: keep the Glintstone repo root tidy.

Blocks commits that drop *new loose Markdown files* into the repo root
outside a small allowed set. Loose planning docs (AUDIT-*, PRD-*, design
notes, etc.) belong under PERSONAL/ (private, untracked) or plan/, not at
the root.

Implementation is deliberately minimal: list the repo root, flag any
unexpected top-level `.md` file. Exit 1 with a clear message if found.

Run manually:  python ops/scripts/check-root-layout.py
Via hook:      pre-commit run check-root-layout --all-files
"""

from __future__ import annotations

import os
import sys

# Markdown files permitted to live at the repo root.
ALLOWED_ROOT_MD = {
    "README.md",
    "CLAUDE.md",
    "AGENTS.md",
    "LEARNINGS.md",
}


def find_stray_root_md(root: str = ".") -> list[str]:
    """Return any top-level *.md files not in the allowed set."""
    stray = []
    for name in os.listdir(root):
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            continue
        if name.endswith(".md") and name not in ALLOWED_ROOT_MD:
            stray.append(name)
    return sorted(stray)


def main() -> int:
    stray = find_stray_root_md()
    if not stray:
        return 0

    allowed = ", ".join(sorted(ALLOWED_ROOT_MD))
    print("✗ check-root-layout: stray Markdown file(s) at the repo root:\n")
    for name in stray:
        print(f"    {name}")
    print(
        "\nLoose planning/design docs do not belong at the repo root.\n"
        "  • Private planning (PRD-*, AUDIT-*, design notes) → PERSONAL/ (untracked)\n"
        "  • Shared planning/design records              → plan/ or plan/design/\n"
        f"\nOnly these Markdown files are allowed at root: {allowed}\n"
        "Move the file(s) above, or extend ALLOWED_ROOT_MD in "
        "ops/scripts/check-root-layout.py if this is intentional."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
