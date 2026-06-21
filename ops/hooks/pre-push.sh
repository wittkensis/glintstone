#!/bin/bash
# Pre-push validation. Warn-only on doc freshness; blocks on invalid YAML.
#
# Rewritten 2026-05-11 for v2 paths.
# 2026-06-21 (#214): added CI-parity gates (ruff format/check, mypy) so the
# same checks that run in .github/workflows/test.yml fail at PUSH time locally,
# not red-on-main after push. Skip if the tool isn't installed; bypass in a
# true emergency with `git push --no-verify` (CLAUDE.md: never push red).

set -e
EXIT_CODE=0

# Resolve a tool binary, preferring the project venv so the local version
# matches the CI pin (ruff==0.15.2). Falls back to PATH, then empty.
resolve_bin() {
    local name="$1"
    if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/$name" ]; then
        echo "$VIRTUAL_ENV/bin/$name"
    elif [ -x "venv/bin/$name" ]; then
        echo "venv/bin/$name"
    elif command -v "$name" >/dev/null 2>&1; then
        command -v "$name"
    else
        echo ""
    fi
}

# CI-parity gates (BLOCKING) — must match the "Lint (ruff)" and
# "Type-check (mypy)" steps in .github/workflows/test.yml exactly.
RUFF_BIN="$(resolve_bin ruff)"
MYPY_BIN="$(resolve_bin mypy)"

if [ -n "$RUFF_BIN" ]; then
    if ! "$RUFF_BIN" format --check .; then
        echo "❌ ruff format --check failed — run: ruff format ."
        EXIT_CODE=1
    fi
    if ! "$RUFF_BIN" check .; then
        echo "❌ ruff check failed — run: ruff check --fix ."
        EXIT_CODE=1
    fi
else
    echo "⚠️  ruff not found — skipping format/lint gate (CI still enforces it). Install: pip install ruff==0.15.2"
fi

if [ -n "$MYPY_BIN" ]; then
    if ! "$MYPY_BIN" api/ app/ core/ mcp/ --ignore-missing-imports; then
        echo "❌ mypy found type errors — fix before pushing."
        EXIT_CODE=1
    fi
else
    echo "⚠️  mypy not found — skipping type gate (CI still enforces it). Install: pip install mypy"
fi

# Schema YAML validity (BLOCKING)
# Use venv python if available so pyyaml is reliably present.
SCHEMA_FILE="data-model/glintstone-schema.yaml"
PYTHON_BIN="${VIRTUAL_ENV:+$VIRTUAL_ENV/bin/python3}"
PYTHON_BIN="${PYTHON_BIN:-$(ls venv/bin/python3 2>/dev/null || echo python3)}"
if [ -f "$SCHEMA_FILE" ]; then
    if ! "$PYTHON_BIN" -c "import yaml; yaml.safe_load(open('$SCHEMA_FILE'))" 2>/dev/null; then
        echo "❌ Schema YAML is invalid: $SCHEMA_FILE"
        EXIT_CODE=1
    fi
fi

# Uncommitted migration files (BLOCKING)
UNCOMMITTED_MIGRATIONS=$(git status --porcelain data-model/migrations/ 2>/dev/null | grep -v '^??' || true)
if [ -n "$UNCOMMITTED_MIGRATIONS" ]; then
    echo "❌ Uncommitted migration files:"
    echo "$UNCOMMITTED_MIGRATIONS"
    EXIT_CODE=1
fi

# Docs freshness (WARN-ONLY)
bash ops/hooks/check-docs-freshness.sh || true

if [ "$EXIT_CODE" -ne 0 ]; then
    echo ""
    echo "Fix the blocking errors above before pushing."
fi

exit "$EXIT_CODE"
