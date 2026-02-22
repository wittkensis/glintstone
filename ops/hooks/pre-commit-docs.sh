#!/bin/bash
# Pre-commit hook: Documentation validation
# Ensures documentation is updated when code changes

set -e

EXIT_CODE=0

echo "Checking documentation consistency..."

# Check if schema changed without docs
if git diff --cached --name-only | grep -q 'data-model/.*\.yaml'; then
    if ! git diff --cached --name-only | grep -qE '(README.md|data-model/.*\.md)'; then
        echo "❌ Schema changed but no documentation updated"
        echo "   Files modified: $(git diff --cached --name-only | grep 'data-model/.*\.yaml' | tr '\n' ' ')"
        echo "   → Update README.md or add docs in data-model/"
        EXIT_CODE=1
    fi
fi

# Check if new import script added without docs
NEW_IMPORTS=$(git diff --cached --name-only --diff-filter=A | grep 'source-data/import-tools/.*\.py' || true)
if [ -n "$NEW_IMPORTS" ]; then
    if ! git diff --cached --name-only | grep -q 'source-data/import-tools/README.md'; then
        echo "❌ New import script added but README not updated"
        echo "   New scripts: $NEW_IMPORTS"
        echo "   → Document in source-data/import-tools/README.md"
        EXIT_CODE=1
    fi
fi

# Check if API routes changed without README update
if git diff --cached --name-only | grep -q 'api/routes/.*\.py'; then
    if ! git diff --cached --name-only | grep -q 'README.md'; then
        echo "⚠️  Warning: API routes changed but README not updated"
        echo "   Consider documenting API changes in README.md"
    fi
fi

# Check for functions without docstrings in staged files
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=AM | grep '\.py$' || true)
if [ -n "$STAGED_PY_FILES" ]; then
    for file in $STAGED_PY_FILES; do
        # Check if file exists (handles renames/deletes)
        if [ -f "$file" ]; then
            # Use simpler pattern: look for function definitions not followed by docstrings
            # This is a basic check - won't catch all cases but avoids complex regex
            if grep -Pzo 'def [a-zA-Z_][a-zA-Z0-9_]*\([^)]*\):\n\s*[^"\s#]' "$file" > /dev/null 2>&1; then
                echo "⚠️  Warning: $file may have functions without docstrings"
            fi
        fi
    done
fi

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Documentation checks passed!"
else
    echo ""
    echo "Fix documentation issues above before committing."
fi

exit $EXIT_CODE
