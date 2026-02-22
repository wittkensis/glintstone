#!/bin/bash
# Pre-push hook: Database schema validation
# Ensures schema changes are valid before pushing

set -e

EXIT_CODE=0

echo "Running pre-push validations..."

# Validate schema YAML if it exists
SCHEMA_FILE="data-model/glintstone-v2-schema.yaml"
if [ -f "$SCHEMA_FILE" ]; then
    echo "→ Validating schema YAML..."
    if ! python3 -c "import yaml; yaml.safe_load(open('$SCHEMA_FILE'))" 2>/dev/null; then
        echo "❌ Schema YAML is invalid: $SCHEMA_FILE"
        EXIT_CODE=1
    else
        echo "✓ Schema YAML is valid"
    fi
else
    echo "⚠️  Schema file not found: $SCHEMA_FILE"
fi

# Check for uncommitted migration files
UNCOMMITTED_MIGRATIONS=$(git status --porcelain data-model/migrations/ 2>/dev/null | grep -v '^??' || true)
if [ -n "$UNCOMMITTED_MIGRATIONS" ]; then
    echo "❌ Uncommitted migration files detected:"
    echo "$UNCOMMITTED_MIGRATIONS"
    echo "   → Commit or stash migration changes before pushing"
    EXIT_CODE=1
fi

# Optional: Dry-run first import script if it exists
# (Commented out by default - can be slow)
# SETUP_SCRIPT="source-data/import-tools/00_setup_database.py"
# if [ -f "$SETUP_SCRIPT" ]; then
#     echo "→ Validating import script SQL..."
#     if ! python3 "$SETUP_SCRIPT" --dry-run 2>/dev/null; then
#         echo "❌ Import script validation failed"
#         EXIT_CODE=1
#     fi
# fi

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ All pre-push checks passed!"
else
    echo ""
    echo "Fix validation errors above before pushing."
fi

exit $EXIT_CODE
