#!/bin/bash
#
# CAD Digitization Setup Script
# =============================
# Installs dependencies and configures API access.
#
# Usage:
#   ./setup.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================================="
echo "CAD DIGITIZATION SETUP"
echo "=============================================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Please install Python 3.10+."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "=============================================================="
    echo "API KEY SETUP"
    echo "=============================================================="
    echo ""
    echo "You need a Google AI Studio API key for Gemini access."
    echo "Get one at: https://aistudio.google.com/apikey"
    echo ""
    read -p "Enter your Google AI Studio API key: " API_KEY

    if [ -z "$API_KEY" ]; then
        echo "WARNING: No API key provided. You can add it later to .env"
        echo "GOOGLE_API_KEY=" > .env
    else
        echo "GOOGLE_API_KEY=$API_KEY" > .env
        echo "API key saved to .env"
    fi
else
    echo ""
    echo ".env file already exists (API key configured)"
fi

# Create checkpoint file
touch .checkpoint

echo ""
echo "=============================================================="
echo "SETUP COMPLETE"
echo "=============================================================="
echo ""
echo "Next steps:"
echo "  1. Run: ./01_download_pdfs.sh"
echo "  2. Run: ./02_pilot_extraction.sh"
echo ""
echo "To activate the virtual environment in a new terminal:"
echo "  source venv/bin/activate"
echo ""
