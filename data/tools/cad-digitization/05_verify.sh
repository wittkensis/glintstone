#!/bin/bash
#
# Verify CAD Extraction
# =====================
# Runs quality checks on the imported CAD data.
#
# Usage:
#   ./05_verify.sh           # Basic verification
#   ./05_verify.sh --verbose # Detailed output
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "=============================================================="
echo "CAD VERIFICATION"
echo "=============================================================="
echo "Started: $(date)"
echo ""

# Run verification
python3 scripts/verify_extraction.py "$@"

EXIT_CODE=$?

echo ""
echo "Finished: $(date)"

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "=============================================================="
    echo "CAD DIGITIZATION PIPELINE COMPLETE"
    echo "=============================================================="
    echo ""
    echo "The CAD data is now available in glintstone.db:"
    echo ""
    echo "  SELECT * FROM cad_entries WHERE headword LIKE 'ab%';"
    echo "  SELECT * FROM cad_entries_summary LIMIT 10;"
    echo "  SELECT * FROM cad_fts WHERE cad_fts MATCH 'king';"
    echo ""
fi

exit $EXIT_CODE
