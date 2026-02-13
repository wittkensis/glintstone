#!/bin/bash
#
# Download CAD PDFs
# =================
# Downloads all 26 Chicago Assyrian Dictionary PDF files.
#
# Usage:
#   ./01_download_pdfs.sh          # Download all volumes
#   ./01_download_pdfs.sh --list   # List available volumes
#   ./01_download_pdfs.sh -v g     # Download specific volume
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Run ./setup.sh first."
    exit 1
fi

echo "=============================================================="
echo "CAD PDF DOWNLOAD"
echo "=============================================================="
echo "Started: $(date)"
echo ""

# Run download script
python3 scripts/download_cad_pdfs.py "$@"

EXIT_CODE=$?

echo ""
echo "Finished: $(date)"

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "Next step: ./02_pilot_extraction.sh"
fi

exit $EXIT_CODE
