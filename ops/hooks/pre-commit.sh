#!/bin/bash
# Pre-commit hook: Python code quality checks
# Runs ruff (linter + formatter) and mypy (type checker) on staged Python files

set -e

# Get list of staged Python files
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

if [ -z "$STAGED_PY_FILES" ]; then
    echo "✓ No Python files staged, skipping quality checks"
    exit 0
fi

echo "Running Python quality checks on staged files..."

# Check if tools are installed
if ! command -v ruff &> /dev/null; then
    echo "❌ ruff not found. Install with: pip install ruff"
    exit 1
fi

if ! command -v mypy &> /dev/null; then
    echo "⚠️  mypy not found. Install with: pip install mypy"
    echo "⚠️  Skipping type checking..."
    SKIP_MYPY=1
fi

# Run ruff check (linting)
echo "→ Running ruff check..."
if ! ruff check $STAGED_PY_FILES; then
    echo "❌ Ruff linting failed. Fix errors above or run: ruff check --fix"
    exit 1
fi

# Note: ruff format is handled by the dedicated ruff-format pre-commit hook

# Run mypy (type checking)
if [ -z "$SKIP_MYPY" ]; then
    echo "→ Running mypy..."
    if ! mypy --ignore-missing-imports $STAGED_PY_FILES; then
        echo "⚠️  Type checking found issues (non-blocking). Fix when practical."
    fi
fi

echo "✓ All Python quality checks passed!"
exit 0
