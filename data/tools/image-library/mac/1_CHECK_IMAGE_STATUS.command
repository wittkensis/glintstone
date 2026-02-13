#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo "CUNEIFORM Image Status Checker"
echo "========================================"
echo ""
echo "This will check ALL 389,715 tablets for images at CDLI."
echo "This takes about 3-5 hours to complete."
echo "You can stop it anytime (Ctrl+C) and resume later."
echo ""
read -p "Press Enter to start..."

cd scripts
python3 check_all_tablets.py

echo ""
echo "Done! Check logs/check_status.log for results."
read -p "Press Enter to close..."
