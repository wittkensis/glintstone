#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo "CUNEIFORM Thumbnail Generator"
echo "========================================"
echo ""
echo "This will generate 4 thumbnail sizes for all images."
echo "Source: images/ folder (uses local files only)"
echo "Output: thumbnails/ folder (~4 GB)"
echo "This takes about 2-3 hours to complete."
echo "You can stop it anytime (Ctrl+C) and resume later."
echo ""
read -p "Press Enter to start..."

cd scripts
python3 generate_thumbnails.py

echo ""
echo "Done! Check logs/thumbnails.log for results."
read -p "Press Enter to close..."
