#!/bin/bash
#
# Full CAD Extraction
# ===================
# Extract all 26 CAD volumes using langextract with Gemini Pro.
# Supports resume if interrupted.
#
# Usage:
#   ./03_full_extraction.sh           # Extract all volumes
#   ./03_full_extraction.sh --resume  # Resume from checkpoint
#   ./03_full_extraction.sh -v k      # Extract specific volume
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

# Parse arguments
RESUME=false
SPECIFIC_VOLUME=""
MODEL="gemini-2.5-pro"
BATCH_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --resume|-r)
            RESUME=true
            shift
            ;;
        --volume|-v)
            SPECIFIC_VOLUME="$2"
            shift 2
            ;;
        --model|-m)
            MODEL="$2"
            shift 2
            ;;
        --batch|-b)
            BATCH_MODE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/full_extraction_$TIMESTAMP.log"
CHECKPOINT_FILE=".extraction_checkpoint"
mkdir -p logs output html

echo "=============================================================="
echo "CAD FULL EXTRACTION"
echo "=============================================================="
echo "Started: $(date)"
echo "Model: $MODEL"
echo "Batch mode: $BATCH_MODE"
echo "Log file: $LOG_FILE"
echo ""

# All volumes in order
VOLUMES=(
    "a1" "a2" "b" "d" "e" "g" "h" "i-j" "k" "l"
    "m1" "m2" "n1" "n2" "p" "q" "r" "s" "s_tsade"
    "s_shin_1" "s_shin_2" "s_shin_3" "t" "tet" "u_w" "z"
)

# Filter to specific volume if requested
if [ -n "$SPECIFIC_VOLUME" ]; then
    VOLUMES=("$SPECIFIC_VOLUME")
fi

# Load checkpoint if resuming
START_INDEX=0
if [ "$RESUME" = true ] && [ -f "$CHECKPOINT_FILE" ]; then
    START_INDEX=$(cat "$CHECKPOINT_FILE")
    echo "Resuming from volume index: $START_INDEX"
fi

# Count total
TOTAL=${#VOLUMES[@]}

# Step 1: Ensure all PDFs are downloaded
echo "[Step 1] Checking PDFs..."
MISSING=0
for vol in "${VOLUMES[@]}"; do
    if [ ! -f "pdfs/cad_$vol.pdf" ]; then
        echo "  Missing: cad_$vol.pdf"
        MISSING=$((MISSING + 1))
    fi
done

if [ $MISSING -gt 0 ]; then
    echo "Downloading $MISSING missing PDFs..."
    python3 scripts/download_cad_pdfs.py 2>&1 | tee -a "$LOG_FILE"
fi

# Step 2: Convert all PDFs to text
echo ""
echo "[Step 2] Converting PDFs to text..."
for vol in "${VOLUMES[@]}"; do
    if [ ! -f "text/cad_$vol.txt" ]; then
        echo "  Converting: cad_$vol.pdf"
        python3 scripts/convert_pdf_to_text.py --volume "$vol" 2>&1 | tee -a "$LOG_FILE"
    else
        echo "  Already converted: cad_$vol.txt"
    fi
done

# Step 3: Extract each volume
echo ""
echo "[Step 3] Extracting entries..."
EXTRACTED=0
ERRORS=0

for i in "${!VOLUMES[@]}"; do
    # Skip if before checkpoint
    if [ $i -lt $START_INDEX ]; then
        continue
    fi

    vol="${VOLUMES[$i]}"
    INPUT="text/cad_$vol.txt"
    OUTPUT="output/cad_$vol.jsonl"
    HTML="html/cad_$vol.html"

    echo ""
    echo "[$((i+1))/$TOTAL] Processing: $vol"

    # Skip if already extracted
    if [ -f "$OUTPUT" ]; then
        LINES=$(wc -l < "$OUTPUT")
        echo "  Already extracted: $LINES entries"
        EXTRACTED=$((EXTRACTED + LINES))
        continue
    fi

    # Check input exists
    if [ ! -f "$INPUT" ]; then
        echo "  ERROR: Input not found: $INPUT"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    # Build extraction command
    EXTRACT_CMD="python3 scripts/run_extraction.py --input $INPUT --output $OUTPUT --html $HTML --model $MODEL"
    if [ "$BATCH_MODE" = true ]; then
        EXTRACT_CMD="$EXTRACT_CMD --batch"
    fi

    # Run extraction
    echo "  Running extraction..."
    if $EXTRACT_CMD 2>&1 | tee -a "$LOG_FILE"; then
        if [ -f "$OUTPUT" ]; then
            LINES=$(wc -l < "$OUTPUT")
            echo "  Extracted: $LINES entries"
            EXTRACTED=$((EXTRACTED + LINES))
        fi
    else
        echo "  ERROR: Extraction failed"
        ERRORS=$((ERRORS + 1))
    fi

    # Save checkpoint
    echo $((i + 1)) > "$CHECKPOINT_FILE"

    # Small delay between volumes to avoid rate limiting
    sleep 2
done

# Step 4: Merge all outputs
echo ""
echo "[Step 4] Merging outputs..."
MERGED_OUTPUT="output/cad_all.jsonl"
cat output/cad_*.jsonl > "$MERGED_OUTPUT" 2>/dev/null || true
TOTAL_ENTRIES=$(wc -l < "$MERGED_OUTPUT" 2>/dev/null || echo "0")
echo "  Total entries: $TOTAL_ENTRIES"

# Summary
echo ""
echo "=============================================================="
echo "EXTRACTION COMPLETE"
echo "=============================================================="
echo "Finished: $(date)"
echo "Total entries extracted: $TOTAL_ENTRIES"
echo "Errors: $ERRORS"
echo ""
echo "Output files:"
echo "  - Individual: output/cad_*.jsonl"
echo "  - Merged: output/cad_all.jsonl"
echo "  - HTML visualizations: html/cad_*.html"
echo ""
echo "Next step: ./04_import_to_db.sh"

# Clear checkpoint on success
if [ $ERRORS -eq 0 ]; then
    rm -f "$CHECKPOINT_FILE"
fi

exit $ERRORS
