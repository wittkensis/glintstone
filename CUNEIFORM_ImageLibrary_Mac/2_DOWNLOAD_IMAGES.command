#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo "CUNEIFORM Image Downloader"
echo "========================================"
echo ""
echo "This will download all available tablet images from CDLI."
echo "Already have ~25k images - will download remaining ones."
echo "This takes about 10-15 hours and uses ~12-15 GB disk space."
echo "You can stop it anytime (Ctrl+C) and resume later."
echo ""
read -p "Press Enter to start..."

cd scripts
python3 download_images.py

echo ""
echo "Done! Check logs/download.log for results."
read -p "Press Enter to close..."
