#!/bin/bash
# Check for unresolved [@Claude ...] feedback comments
# This script helps find active feedback that needs to be addressed

echo "🔍 Checking for unresolved feedback comments..."
echo ""

# Search for [@Claude or [@agent but exclude struck-through ones
RESULTS=$(grep -rn "\[@" docs/ Instructions/ --include="*.md" 2>/dev/null | grep -v "~~\[@" | grep -E "\[@Claude|\[@[a-z]+-[a-z]+")

if [ -z "$RESULTS" ]; then
    echo "✅ No unresolved feedback comments found!"
    exit 0
else
    echo "⚠️  Found unresolved feedback comments:"
    echo ""
    echo "$RESULTS"
    echo ""
    echo "💡 Remember to mark as resolved using strikethrough: ~~[@Claude ...]~~"
    exit 1
fi
