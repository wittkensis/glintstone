#!/usr/bin/env bash
#
# Citation Import Pipeline Orchestrator
#
# Runs all citation import phases in dependency order.
# Each phase is idempotent and supports --reset for clean re-run.
#
# Usage:
#   ./run_citation_import.sh [--reset]
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESET_FLAG="${1:-}"
PYTHON="${SCRIPT_DIR}/../../../venv/bin/python3"

echo "════════════════════════════════════════════════════════════"
echo "  GLINTSTONE CITATION IMPORT PIPELINE"
echo "  Database: PostgreSQL (from .env settings)"
echo "════════════════════════════════════════════════════════════"
echo ""

run_phase() {
    local script="$1"
    local name="$2"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Phase: $name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if "$PYTHON" "$SCRIPT_DIR/$script" $RESET_FLAG; then
        echo "  ✓ $name completed"
    else
        echo "  ✗ $name failed (exit code $?)"
        echo "  Pipeline paused. Fix the issue and re-run."
        exit 1
    fi
    echo ""
}

# Phase 1: CDLI Publications (foundation — must run first)
run_phase "01_cdli_publications.py" "CDLI Publications"

# Phase 1B+1C: CDLI Artifact Editions (depends on publications)
run_phase "02_cdli_artifact_editions.py" "CDLI Artifact Editions"

# Phase 2: eBL Bibliography (independent of CDLI editions)
run_phase "03_ebl_bibliography.py" "eBL Bibliography"

# Phase 3: ORACC Editions (independent)
run_phase "04_oracc_editions.py" "ORACC Editions"

# Phase 4: CDLI CSV Supplementary (depends on publications)
run_phase "05_cdli_csv_supplementary.py" "CDLI CSV Supplementary"

# Phase 5: OpenAlex Enrichment (enriches existing publications + scholars)
run_phase "06_enrich_openalex.py" "OpenAlex Enrichment"

# Phase 6: KeiBi (if data available — will skip gracefully if no .bib files)
run_phase "07_import_keibi.py" "KeiBi Bibliography"

# Phase 7: Semantic Scholar (optional enrichment)
run_phase "08_enrich_semantic_scholar.py" "Semantic Scholar"

# Phase 8: Scholar Directory
run_phase "09_import_scholars_directory.py" "Scholar Directory"

# Phase 9: Supersession Chains (must run last — needs all editions)
run_phase "10_seed_supersessions.py" "Supersession Chains"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  VERIFICATION"
echo "════════════════════════════════════════════════════════════"
echo ""

"$PYTHON" "$SCRIPT_DIR/verify/verify_publications.py"
echo ""
"$PYTHON" "$SCRIPT_DIR/verify/verify_provider_attribution.py"
echo ""
"$PYTHON" "$SCRIPT_DIR/verify/verify_artifact_editions.py"
echo ""
"$PYTHON" "$SCRIPT_DIR/verify/verify_scholars.py"
echo ""
"$PYTHON" "$SCRIPT_DIR/verify/verify_dedup.py"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  PIPELINE COMPLETE"
echo "════════════════════════════════════════════════════════════"
