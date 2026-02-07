#!/bin/bash
#
# Full CDLI Import Script
# =======================
# Imports complete CDLI catalog (353K+ tablets) and ATF inscriptions.
# Supports resume on interruption - safe to run multiple times.
#
# Usage:
#   ./run_full_import.sh          # Normal run (resumes if interrupted)
#   ./run_full_import.sh --reset  # Start fresh, ignore checkpoints
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_DIR="$BASE_DIR/_logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create log directory
mkdir -p "$LOG_DIR"

# Parse arguments
RESET_FLAG=""
if [[ "$1" == "--reset" ]]; then
    RESET_FLAG="--reset"
    echo "=== RESET MODE: Starting fresh import ==="
fi

echo "=============================================================="
echo "CDLI FULL IMPORT"
echo "=============================================================="
echo "Started: $(date)"
echo "Base directory: $BASE_DIR"
echo "Logs: $LOG_DIR"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

# Step 1: Import catalog from CSV
echo ""
echo "[Step 1/3] Importing CDLI catalog from CSV..."
echo "--------------------------------------------------------------"
python3 "$SCRIPT_DIR/import_cdli_catalog.py" $RESET_FLAG 2>&1 | tee "$LOG_DIR/import_catalog_$TIMESTAMP.log"

CATALOG_EXIT=$?
if [[ $CATALOG_EXIT -ne 0 ]]; then
    echo ""
    echo "WARNING: Catalog import exited with code $CATALOG_EXIT"
    echo "This may be due to interruption. Run again to resume."
    exit $CATALOG_EXIT
fi

# Step 2: Import ATF inscriptions
echo ""
echo "[Step 2/3] Importing ATF inscriptions..."
echo "--------------------------------------------------------------"
python3 "$SCRIPT_DIR/import_cdli_atf.py" $RESET_FLAG 2>&1 | tee "$LOG_DIR/import_atf_$TIMESTAMP.log"

ATF_EXIT=$?
if [[ $ATF_EXIT -ne 0 ]]; then
    echo ""
    echo "WARNING: ATF import exited with code $ATF_EXIT"
    echo "This may be due to interruption. Run again to resume."
    exit $ATF_EXIT
fi

# Step 3: Verify import
echo ""
echo "[Step 3/3] Verifying import..."
echo "--------------------------------------------------------------"
python3 "$BASE_DIR/data-tools/validate/verify_cdli_import.py" --verbose 2>&1 | tee "$LOG_DIR/verify_$TIMESTAMP.log"

VERIFY_EXIT=$?

echo ""
echo "=============================================================="
echo "IMPORT COMPLETE"
echo "=============================================================="
echo "Finished: $(date)"
echo "Verification: $([ $VERIFY_EXIT -eq 0 ] && echo 'PASSED' || echo 'FAILED')"
echo ""
echo "Logs saved to: $LOG_DIR"
echo ""

# Quick summary
echo "Quick database check:"
sqlite3 "$BASE_DIR/database/glintstone.db" "
    SELECT 'Artifacts:' as label, COUNT(*) as count FROM artifacts
    UNION ALL
    SELECT 'Elamite:', COUNT(*) FROM artifacts WHERE LOWER(language) LIKE '%elamite%'
    UNION ALL
    SELECT 'Inscriptions:', COUNT(*) FROM inscriptions
    UNION ALL
    SELECT 'With ATF:', COUNT(*) FROM pipeline_status WHERE has_atf = 1;
"

exit $VERIFY_EXIT
