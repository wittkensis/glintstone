#!/bin/bash
# Verify v2 ingestion-framework integrity.
# Called by Claude Code Stop hook.
#
# Rewritten 2026-05-11 to target the v2 framework instead of the retired v1
# numbered scripts in source-data/import-tools/.

set -e

EXIT_CODE=0

echo "Verifying v2 ingestion framework integrity..."

# Schema YAML
SCHEMA_FILE="data-model/v2/glintstone-v2-schema.yaml"
if [ -f "$SCHEMA_FILE" ]; then
    echo "→ Validating $SCHEMA_FILE..."
    if ! python3 -c "import yaml; yaml.safe_load(open('$SCHEMA_FILE'))" 2>/dev/null; then
        echo "❌ Schema YAML is invalid: $SCHEMA_FILE"
        EXIT_CODE=1
    else
        echo "✓ Schema YAML is valid"
    fi
else
    echo "⚠ Schema YAML not found at $SCHEMA_FILE"
fi

# Validate Python syntax for ingestion framework + connectors
INGESTION_DIR="ingestion"
if [ -d "$INGESTION_DIR" ]; then
    echo "→ Validating Python syntax in $INGESTION_DIR/..."
    SCRIPT_COUNT=0
    ERROR_COUNT=0
    while IFS= read -r script; do
        SCRIPT_COUNT=$((SCRIPT_COUNT + 1))
        if ! python3 -m py_compile "$script" 2>/dev/null; then
            echo "❌ Syntax error in: $script"
            ERROR_COUNT=$((ERROR_COUNT + 1))
            EXIT_CODE=1
        fi
    done < <(find "$INGESTION_DIR" -name "*.py" -not -path '*/__pycache__/*')
    if [ "$ERROR_COUNT" -eq 0 ]; then
        echo "✓ All $SCRIPT_COUNT v2 ingestion files parse cleanly"
    else
        echo "❌ Found $ERROR_COUNT scripts with syntax errors out of $SCRIPT_COUNT"
    fi

    # Light registry sanity check — only if a venv exists
    if [ -x "venv/bin/python" ]; then
        echo "→ Checking the connector registry loads..."
        if venv/bin/python -c "from ingestion.registry import discover_connectors; cs = discover_connectors(); print(f'  {len(cs)} connector(s) registered')" 2>/dev/null; then
            true
        else
            echo "⚠ Registry didn't load — likely DATABASE_URL or import-path issue. Not blocking."
        fi
    fi
fi

# Uncommitted changes in ingestion or migrations
for path in "$INGESTION_DIR" "source-data/migrations"; do
    if [ -d "$path" ]; then
        UNCOMMITTED=$(git status --porcelain "$path" 2>/dev/null | grep -v '^??' || true)
        if [ -n "$UNCOMMITTED" ]; then
            echo "⚠ Uncommitted changes in $path:"
            echo "$UNCOMMITTED" | sed 's/^/    /'
        fi
    fi
done

if [ "$EXIT_CODE" -eq 0 ]; then
    echo "✓ v2 ingestion integrity verified."
else
    echo ""
    echo "Fix issues above before ending the session."
fi

exit "$EXIT_CODE"
