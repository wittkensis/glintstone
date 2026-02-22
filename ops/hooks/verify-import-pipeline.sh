#!/bin/bash
# Verify import pipeline integrity
# Called by Claude Code Stop hook to ensure import scripts haven't broken

set -e

EXIT_CODE=0

echo "Verifying import pipeline integrity..."

# Check if any import tools were modified in this session
IMPORT_TOOLS_DIR="source-data/import-tools"

if [ ! -d "$IMPORT_TOOLS_DIR" ]; then
    echo "✓ Import tools directory not found, skipping validation"
    exit 0
fi

# Check if there are uncommitted changes in import tools
UNCOMMITTED=$(git status --porcelain "$IMPORT_TOOLS_DIR" 2>/dev/null | grep -v '^??' || true)
if [ -n "$UNCOMMITTED" ]; then
    echo "⚠️  Uncommitted changes in import tools:"
    echo "$UNCOMMITTED"
    echo "   → Commit changes before ending session"
    EXIT_CODE=1
fi

# Validate all Python import scripts parse correctly
echo "→ Validating Python syntax for all import scripts..."
SCRIPT_COUNT=0
ERROR_COUNT=0

for script in "$IMPORT_TOOLS_DIR"/*.py; do
    if [ -f "$script" ]; then
        SCRIPT_COUNT=$((SCRIPT_COUNT + 1))
        if ! python3 -m py_compile "$script" 2>/dev/null; then
            echo "❌ Syntax error in: $script"
            ERROR_COUNT=$((ERROR_COUNT + 1))
            EXIT_CODE=1
        fi
    fi
done

if [ $ERROR_COUNT -eq 0 ]; then
    echo "✓ All $SCRIPT_COUNT import scripts have valid Python syntax"
else
    echo "❌ Found $ERROR_COUNT scripts with syntax errors out of $SCRIPT_COUNT"
fi

# Validate schema YAML
SCHEMA_FILE="data-model/glintstone-v2-schema.yaml"
if [ -f "$SCHEMA_FILE" ]; then
    echo "→ Validating schema YAML..."
    if ! python3 -c "import yaml; yaml.safe_load(open('$SCHEMA_FILE'))" 2>/dev/null; then
        echo "❌ Schema YAML is invalid: $SCHEMA_FILE"
        EXIT_CODE=1
    else
        echo "✓ Schema YAML is valid"
    fi
fi

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Import pipeline integrity verified!"
else
    echo ""
    echo "Fix pipeline issues above before ending session."
fi

exit $EXIT_CODE
