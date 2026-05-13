#!/bin/bash
# Pre-commit hook: mypy type-checking on staged Python files (warn-only).
# Ruff lint + format is handled by the astral-sh/ruff-precommit hooks in
# .pre-commit-config.yaml, which run after this and auto-fix. Don't add ruff
# here — it would block before the fixer can run.

STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

if [ -z "$STAGED_PY_FILES" ]; then
    exit 0
fi

if ! command -v mypy &> /dev/null; then
    exit 0
fi

echo "→ Running mypy (warn-only)..."
# shellcheck disable=SC2086
if ! mypy --ignore-missing-imports $STAGED_PY_FILES 2>/dev/null; then
    echo "⚠️  mypy found type issues — fix when practical, commit proceeds."
fi

exit 0
