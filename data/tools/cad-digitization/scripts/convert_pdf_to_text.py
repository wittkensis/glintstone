#!/usr/bin/env python3
"""
Convert CAD PDFs to text with two-column layout handling.

Usage:
    python convert_pdf_to_text.py pdfs/cad_g.pdf
    python convert_pdf_to_text.py --all
    python convert_pdf_to_text.py --volume g

The script:
1. Extracts text from PDF using pdfplumber
2. Handles two-column layout by detecting column boundaries
3. Skips front matter (title pages, prefaces, etc.)
4. Outputs clean text files ready for langextract
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip install pdfplumber")
    sys.exit(1)


# Front matter detection - pages before actual dictionary entries
# These patterns indicate we're still in front matter
FRONT_MATTER_PATTERNS = [
    r'^FOREWORD',
    r'^PREFACE',
    r'^INTRODUCTION',
    r'^TABLE OF CONTENTS',
    r'^CONTENTS',
    r'^ABBREVIATIONS',
    r'^BIBLIOGRAPHY',
    r'^PROVISIONAL LIST',
    r'^LIST OF',
    r'^\s*i+\s*$',  # Roman numeral page numbers
    r'^\s*v+i*\s*$',
]

# Entry header pattern - indicates start of dictionary content
# Entries start with bold headword followed by grammatical info
ENTRY_START_PATTERN = re.compile(
    r'^[a-zšṣṭḫāēīū][a-zšṣṭḫāēīū\-\']+\s+(?:s\.|v\.|adj\.|adv\.|prep\.|conj\.)',
    re.IGNORECASE
)


def is_front_matter(text: str) -> bool:
    """Check if page text is front matter."""
    first_lines = '\n'.join(text.strip().split('\n')[:5])
    for pattern in FRONT_MATTER_PATTERNS:
        if re.search(pattern, first_lines, re.IGNORECASE):
            return True
    return False


def has_entry_start(text: str) -> bool:
    """Check if page contains dictionary entry starts."""
    for line in text.split('\n')[:30]:  # Check first 30 lines
        if ENTRY_START_PATTERN.match(line.strip()):
            return True
    return False


def extract_columns(page) -> str:
    """
    Extract text from a two-column page.

    Uses pdfplumber's ability to extract text with layout preservation,
    then splits into columns based on x-coordinates.
    """
    # Get page dimensions
    width = page.width
    height = page.height
    mid_x = width / 2

    # Define column bounding boxes with small margin
    margin = 10
    left_bbox = (0, 0, mid_x - margin, height)
    right_bbox = (mid_x + margin, 0, width, height)

    # Extract text from each column
    left_text = page.within_bbox(left_bbox).extract_text() or ""
    right_text = page.within_bbox(right_bbox).extract_text() or ""

    # Combine columns (left first, then right)
    return left_text + "\n\n" + right_text


def extract_single_column(page) -> str:
    """Extract text as single column (for pages that aren't two-column)."""
    return page.extract_text() or ""


def detect_layout(page) -> str:
    """Detect if page is single or two-column layout."""
    # Simple heuristic: check if there's a vertical gap in the middle
    words = page.extract_words()
    if not words:
        return "empty"

    mid_x = page.width / 2
    margin = 30  # pixels

    # Count words in the middle zone
    middle_words = [w for w in words if mid_x - margin < w['x0'] < mid_x + margin]

    # If very few words cross the middle, it's likely two-column
    if len(middle_words) < len(words) * 0.05:
        return "two_column"
    return "single_column"


def convert_pdf(pdf_path: Path, output_dir: Path, skip_front_matter: bool = True) -> dict:
    """
    Convert a CAD PDF to text.

    Returns:
        dict with statistics about the conversion
    """
    output_path = output_dir / (pdf_path.stem + ".txt")

    stats = {
        "input_file": str(pdf_path),
        "output_file": str(output_path),
        "total_pages": 0,
        "front_matter_pages": 0,
        "content_pages": 0,
        "first_content_page": None,
    }

    print(f"Converting: {pdf_path.name}")

    with pdfplumber.open(pdf_path) as pdf:
        stats["total_pages"] = len(pdf.pages)
        all_text = []
        in_content = False

        for i, page in enumerate(pdf.pages):
            page_num = i + 1

            # Detect layout and extract text
            layout = detect_layout(page)

            if layout == "empty":
                continue
            elif layout == "two_column":
                text = extract_columns(page)
            else:
                text = extract_single_column(page)

            # Check for front matter
            if skip_front_matter and not in_content:
                if is_front_matter(text):
                    stats["front_matter_pages"] += 1
                    continue

                # Check if we've reached actual entries
                if has_entry_start(text):
                    in_content = True
                    stats["first_content_page"] = page_num
                    print(f"  Content starts at page {page_num}")
                else:
                    stats["front_matter_pages"] += 1
                    continue

            # Add page marker and content
            all_text.append(f"\n\n--- PAGE {page_num} ---\n\n")
            all_text.append(text)
            stats["content_pages"] += 1

            # Progress indicator
            if page_num % 50 == 0:
                print(f"  Processed page {page_num}/{stats['total_pages']}")

    # Write output
    output_text = ''.join(all_text)
    output_path.write_text(output_text, encoding='utf-8')

    print(f"  Output: {output_path.name}")
    print(f"  Pages: {stats['content_pages']} content, {stats['front_matter_pages']} skipped")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Convert CAD PDFs to text")
    parser.add_argument("pdf_file", nargs="?", help="Specific PDF file to convert")
    parser.add_argument("--all", "-a", action="store_true", help="Convert all PDFs in pdfs/")
    parser.add_argument("--volume", "-v", help="Convert specific volume by ID (e.g., 'g', 'a1')")
    parser.add_argument("--no-skip-front", action="store_true", help="Don't skip front matter")
    args = parser.parse_args()

    script_dir = Path(__file__).parent.parent
    pdfs_dir = script_dir / "pdfs"
    text_dir = script_dir / "text"
    text_dir.mkdir(exist_ok=True)

    # Determine which PDFs to convert
    if args.pdf_file:
        pdf_files = [Path(args.pdf_file)]
    elif args.volume:
        pattern = f"cad_{args.volume.lower()}*.pdf"
        pdf_files = list(pdfs_dir.glob(pattern))
        if not pdf_files:
            print(f"ERROR: No PDF found matching '{pattern}'")
            return 1
    elif args.all:
        pdf_files = sorted(pdfs_dir.glob("cad_*.pdf"))
        if not pdf_files:
            print("ERROR: No PDFs found in pdfs/ directory")
            print("Run ./01_download_pdfs.sh first")
            return 1
    else:
        parser.print_help()
        return 1

    print("=" * 60)
    print("CAD PDF TO TEXT CONVERSION")
    print("=" * 60)
    print(f"Output directory: {text_dir}")
    print(f"Files to convert: {len(pdf_files)}")
    print()

    all_stats = []
    for pdf_file in pdf_files:
        stats = convert_pdf(pdf_file, text_dir, not args.no_skip_front)
        all_stats.append(stats)
        print()

    # Save conversion stats
    stats_path = text_dir / "conversion_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(all_stats, f, indent=2)

    # Summary
    total_content = sum(s["content_pages"] for s in all_stats)
    total_skipped = sum(s["front_matter_pages"] for s in all_stats)
    print("=" * 60)
    print("CONVERSION COMPLETE")
    print("=" * 60)
    print(f"  Total content pages: {total_content}")
    print(f"  Total skipped pages: {total_skipped}")
    print(f"  Stats saved to: {stats_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
