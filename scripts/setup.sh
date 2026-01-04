#!/bin/bash

# Glintstone Tablet Scripts Setup
# Run this once to set up the directory structure and make scripts executable

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "=== Glintstone Tablet Scripts Setup ==="
echo "Project root: $PROJECT_ROOT"
echo ""

# Make scripts executable
echo "Making scripts executable..."
chmod +x "$SCRIPT_DIR/download-tablets.js"
chmod +x "$SCRIPT_DIR/update-metadata.js"
chmod +x "$SCRIPT_DIR/organize-tablets.js"
echo "✓ Scripts are now executable"
echo ""

# Create directory structure
echo "Creating directory structure..."
mkdir -p "$PROJECT_ROOT/data/tablets"
mkdir -p "$PROJECT_ROOT/public/images/tablets/authentic"
mkdir -p "$PROJECT_ROOT/public/images/tablets/organized"
echo "✓ Directories created"
echo ""

# Check Node.js version
echo "Checking Node.js version..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✓ Node.js $NODE_VERSION is installed"
else
    echo "✗ Node.js is not installed. Please install Node.js 14+ to use these scripts."
    exit 1
fi
echo ""

# Test connectivity to CDLI
echo "Testing connectivity to CDLI..."
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "https://cdli.earth/dl/photo/P005377.jpg")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✓ CDLI is reachable"
    else
        echo "! CDLI returned HTTP $HTTP_CODE (this may be normal, continuing...)"
    fi
else
    echo "! curl not found, skipping connectivity test"
fi
echo ""

echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit tablet-list.txt with your desired P-numbers"
echo "  2. Run: node scripts/download-tablets.js --file scripts/tablet-list.txt"
echo "  3. Run: node scripts/update-metadata.js to add detailed metadata"
echo "  4. Run: node scripts/organize-tablets.js all"
echo ""
echo "For help, see: scripts/README.md"
