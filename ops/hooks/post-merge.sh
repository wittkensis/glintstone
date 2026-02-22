#!/bin/bash
# Post-merge hook: Dependency sync warnings
# Alerts when dependencies or config change after merge

echo "Checking for dependency/config changes..."

# Check if requirements.txt changed
if git diff HEAD@{1} HEAD --name-only 2>/dev/null | grep -q requirements.txt; then
    echo ""
    echo "⚠️  requirements.txt changed after merge!"
    echo "   → Run: pip install -r requirements.txt"
    echo ""
fi

# Check if .env.example changed
if git diff HEAD@{1} HEAD --name-only 2>/dev/null | grep -q '.env.example'; then
    echo ""
    echo "⚠️  .env.example changed after merge!"
    echo "   → Review and update your .env file"
    echo ""
fi

# Check if data-model changed
if git diff HEAD@{1} HEAD --name-only 2>/dev/null | grep -q 'data-model/'; then
    echo ""
    echo "⚠️  Data model changed after merge!"
    echo "   → Review migrations in data-model/migrations/"
    echo "   → Run migration script if needed"
    echo ""
fi

# Check if ops/local scripts changed
if git diff HEAD@{1} HEAD --name-only 2>/dev/null | grep -q 'ops/local/'; then
    echo ""
    echo "⚠️  Local development scripts changed!"
    echo "   → Review changes in ops/local/"
    echo "   → Restart dev servers if needed: ops/local/stop.sh && ops/local/start.sh"
    echo ""
fi

exit 0
