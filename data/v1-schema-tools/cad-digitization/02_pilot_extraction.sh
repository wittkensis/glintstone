#!/bin/bash
#
# Pilot Extraction
# ================
# Test extraction on the smallest volume (cad_g.pdf, 158 pages)
# to validate the schema and prompts before full extraction.
#
# Usage:
#   ./02_pilot_extraction.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "ERROR: Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

# Check for API key
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found. Run ./setup.sh first."
    exit 1
fi

source .env
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "ERROR: GOOGLE_API_KEY not set in .env"
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/pilot_$TIMESTAMP.log"
mkdir -p logs

echo "=============================================================="
echo "CAD PILOT EXTRACTION"
echo "=============================================================="
echo "Started: $(date)"
echo "Log file: $LOG_FILE"
echo ""

# Step 1: Check for pilot PDF
PILOT_PDF="pdfs/cad_g.pdf"
if [ ! -f "$PILOT_PDF" ]; then
    echo "[Step 1] Downloading pilot volume (cad_g)..."
    python3 scripts/download_cad_pdfs.py --volume g 2>&1 | tee -a "$LOG_FILE"
fi

# Step 2: Convert PDF to text
echo ""
echo "[Step 2] Converting PDF to text..."
python3 scripts/convert_pdf_to_text.py --volume g 2>&1 | tee -a "$LOG_FILE"

# Step 3: Check for examples file
EXAMPLES_FILE="config/examples.json"
if [ ! -f "$EXAMPLES_FILE" ]; then
    echo ""
    echo "=============================================================="
    echo "MANUAL STEP REQUIRED"
    echo "=============================================================="
    echo ""
    echo "Before running extraction, you need to create few-shot examples."
    echo ""
    echo "1. Open a CAD PDF (e.g., pdfs/cad_g.pdf)"
    echo "2. Find 5-10 representative entries"
    echo "3. Create config/examples.json with the structure shown in README"
    echo ""
    echo "A stub file has been created at: $EXAMPLES_FILE"
    echo "Edit it with real examples, then re-run this script."
    echo ""

    # Create stub examples file
    mkdir -p config
    cat > "$EXAMPLES_FILE" << 'EOF'
{
  "description": "Few-shot examples for CAD entry extraction",
  "note": "Replace these with real examples from the CAD PDFs",
  "examples": [
    {
      "input_text": "gamālu v.; to spare, show mercy; ...",
      "expected_output": {
        "headword": "gamālu",
        "part_of_speech": "v.",
        "meanings": [
          {
            "position": "a",
            "definition": "to spare, show mercy"
          }
        ]
      }
    }
  ]
}
EOF
    exit 0
fi

# Step 4: Run extraction
echo ""
echo "[Step 4] Running langextract on pilot volume..."
python3 scripts/run_extraction.py \
    --input text/cad_g.txt \
    --output output/cad_g_pilot.jsonl \
    --html html/cad_g_pilot.html \
    --model gemini-2.0-flash \
    2>&1 | tee -a "$LOG_FILE"

# Step 5: Show results summary
echo ""
echo "[Step 5] Extraction summary..."
if [ -f "output/cad_g_pilot.jsonl" ]; then
    ENTRY_COUNT=$(wc -l < "output/cad_g_pilot.jsonl")
    echo "  Entries extracted: $ENTRY_COUNT"
    echo "  Output file: output/cad_g_pilot.jsonl"
    echo "  HTML visualization: html/cad_g_pilot.html"
    echo ""
    echo "Sample entries:"
    head -3 "output/cad_g_pilot.jsonl" | python3 -m json.tool 2>/dev/null || head -3 "output/cad_g_pilot.jsonl"
fi

echo ""
echo "=============================================================="
echo "PILOT EXTRACTION COMPLETE"
echo "=============================================================="
echo "Finished: $(date)"
echo ""
echo "NEXT STEPS:"
echo "  1. Review html/cad_g_pilot.html to verify source grounding"
echo "  2. Check output/cad_g_pilot.jsonl for extraction quality"
echo "  3. Adjust config/examples.json if needed"
echo "  4. When satisfied, run: ./03_full_extraction.sh"
echo ""
