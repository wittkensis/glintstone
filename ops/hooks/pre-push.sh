#!/bin/bash
# Pre-push validation. Warn-only on doc freshness; blocks on invalid YAML.
#
# Rewritten 2026-05-11 for v2 paths.

set -e
EXIT_CODE=0

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
