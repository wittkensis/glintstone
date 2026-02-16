#!/bin/bash
#
# Import CAD Data to Database
# ===========================
# Imports extracted CAD entries into glintstone.db.
#
# Usage:
#   ./04_import_to_db.sh          # Import all extracted data
#   ./04_import_to_db.sh --reset  # Clear and reimport
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/import_$TIMESTAMP.log"
mkdir -p logs

echo "=============================================================="
echo "CAD DATABASE IMPORT"
echo "=============================================================="
echo "Started: $(date)"
echo "Log file: $LOG_FILE"
echo ""

# Check for extraction output
if [ ! -d "output" ] || [ -z "$(ls -A output/*.jsonl 2>/dev/null)" ]; then
    echo "ERROR: No extraction output found in output/"
    echo "Run ./03_full_extraction.sh first"
    exit 1
fi

# Count files
FILE_COUNT=$(ls output/cad_*.jsonl 2>/dev/null | wc -l)
echo "Found $FILE_COUNT extraction files"
echo ""

# Run import
python3 scripts/import_cad_entries.py --all "$@" 2>&1 | tee "$LOG_FILE"

EXIT_CODE=$?

echo ""
echo "Finished: $(date)"

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "Next step: ./05_verify.sh"
fi

exit $EXIT_CODE
