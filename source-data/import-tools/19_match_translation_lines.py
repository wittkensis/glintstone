#!/usr/bin/env python3
"""
Step 19: Match translations to text_lines by parsing line number hints.

Parses line number prefixes from translation text and matches to text_lines.line_number.
Uses heuristic patterns to extract line numbers, surfaces, and positional fallback.

=== MATCHING STRATEGY ===

PHASE 1: Unmatchable Classification
  Identifies non-content translations before matching:
  - Broken/damaged: "...", "22 ... slaves" (embedded ellipsis)
  - Placeholder: "xxx", "xxxx"
  - Metadata: "Basket-of-tablets:", "total:", section headers

PHASE 2: Pattern-Based Extraction
  Extracts line references using regex patterns (ordered by priority):
  0. Sub-line notation: "1.a.", "2.b" → matches "1.a", "2.b" (0.7 confidence)
  1. Surface + line: "o 1.", "r i 3'" → with surface (1.0 confidence)
  2. Line only: "1.", "12'" → without surface (0.8 confidence)
  3. Reversed: "1 o." → reversed notation (0.9 confidence)
  4. Prime: "1'" → primed lines (0.75 confidence)

PHASE 3: Database Matching
  Looks up text_lines by (p_number, surface, line_number)
  Stores match with confidence score

PHASE 4: Positional Fallback
  For translations with no extractable line reference,
  matches by position: translation index → text_line offset (0.5 confidence)

LIMITATIONS:
  - Sub-line structure (1.a, 1.b) may cause many-to-one mappings
  - Positional fallback fails when translation count > line count
  - Some unmatched entries are inherent to ATF structure, not errors

Depends on:
  - Step 3 (text_lines table populated)
  - Step 15 (translations table populated)

Usage:
    python 19_match_translation_lines.py [--reset] [--limit N]
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from psycopg.rows import dict_row
from core.config import get_settings

# Add citations/lib to path for checkpoint
citations_lib = Path(__file__).parent / "citations" / "lib"
sys.path.insert(0, str(citations_lib))

from checkpoint import ImportCheckpoint  # noqa: E402


# Patterns for non-matchable translations (must classify BEFORE attempting line matching)
UNMATCHABLE_PATTERNS = [
    # ENHANCED: Catches any ellipsis - standalone, leading, embedded, or trailing
    # Examples: "...", "22 ... slaves", "... field", "word ... word"
    (r"(^\.{3,}|^\.{3,}\s+|\s\.{3,}\s|\s\.{3,}$)", "broken"),
    (r"^x{3,}\s*$", "placeholder"),  # xxx, xxxx, etc.
    (r"^Basket-of-tablets:", "metadata"),
    (r"^total:", "summary"),
    (r"^received\.?\s*$", "summary"),
    (r"^(obverse|reverse|edge|left edge|right edge)\s*:\s*$", "section_header"),
]

# Regex patterns for line number extraction
SURFACE_MAP = {
    "o": "obverse",
    "r": "reverse",
    "e": "edge",
    "obv": "obverse",
    "rev": "reverse",
    "obverse": "obverse",
    "reverse": "reverse",
    "edge": "edge",
}

PATTERNS = [
    # Pattern 0: Sub-line notation "1.a. text", "2.b text", or "o 3.c. text"
    # ENHANCED: Handles sub-line notation from parser fix
    # NOTE: After parser re-import, text_lines will have "1.a", "1.b" etc.,
    # so this pattern now matches them directly
    (
        r"^([oro]|obv?|rev?|obverse|reverse|edge)?\s*(\d+)\.([a-z]\d?)\s*[.:]\s*(.+)$",
        lambda m: {
            "surface": SURFACE_MAP.get(m.group(1).lower(), None)
            if m.group(1)
            else None,
            "line_number": m.group(2)
            + "."
            + m.group(3),  # Full line number with sub-line
            "confidence": 0.7,  # Lower confidence (many-to-one possible)
        },
    ),
    # Pattern 1: "o 1. text" or "o i 3' text" (surface + optional column + line)
    (
        r"^([oro]|obv?|rev?|obverse|reverse|edge)\s+([ivxIVX]*)\s*(\d+)[\'\s]*[.:]\s*(.+)$",
        lambda m: {
            "surface": SURFACE_MAP.get(m.group(1).lower(), m.group(1).lower()),
            "line_number": m.group(3),
            "confidence": 1.0,
        },
    ),
    # Pattern 2: "1. text" (line number only)
    (
        r"^\s*(\d+)[\'\s]*[.:]\s*(.+)$",
        lambda m: {"line_number": m.group(1), "confidence": 0.8},
    ),
    # Pattern 3: "obverse 1" (full surface name)
    (
        r"^(obverse|reverse|edge)\s+(\d+)[\'\s]*[.:]\s*(.+)$",
        lambda m: {"surface": m.group(1), "line_number": m.group(2), "confidence": 1.0},
    ),
    # Pattern 4: Reversed surface notation "1 o." or "1 r."
    (
        r"^\s*(\d+)[\'\s]*\s+([oro]|obv?|rev?)\s*[.:]\s*(.+)$",
        lambda m: {
            "line_number": m.group(1),
            "surface": SURFACE_MAP.get(m.group(2).lower(), m.group(2).lower()),
            "confidence": 0.9,
        },
    ),
    # Pattern 5: Line with apostrophe "1' text" (primed line numbers)
    (
        r"^\s*(\d+)[\'][\s:\.]\s*(.+)$",
        lambda m: {"line_number": m.group(1), "confidence": 0.75},
    ),
]


def classify_unmatchable(translation_text: str) -> str | None:
    """
    Check if translation is non-matchable content (not a line translation).

    Returns unmatchable_type if translation is non-content, None otherwise.
    """
    for pattern, classification in UNMATCHABLE_PATTERNS:
        if re.match(pattern, translation_text, re.IGNORECASE):
            return classification
    return None


def extract_line_info(translation_text: str) -> dict | None:
    """
    Extract line number and surface from translation text.

    Returns dict with:
        line_number, surface (optional), confidence
    or None if no pattern matches.
    """
    for pattern, extractor in PATTERNS:
        m = re.match(pattern, translation_text, re.IGNORECASE)
        if m:
            try:
                return extractor(m)
            except (IndexError, AttributeError):
                continue
    return None


def match_translation_to_line(
    conn, p_number: str, line_info: dict
) -> tuple[int | None, float]:
    """
    Match translation to text_line using line_info.

    Returns (line_id, confidence).
    """
    line_number = line_info["line_number"]
    surface = line_info.get("surface")
    confidence = line_info["confidence"]

    if surface:
        # Prefer surface + line match
        result = conn.execute(
            """
            SELECT tl.id FROM text_lines tl
            JOIN surfaces s ON tl.surface_id = s.id
            WHERE tl.p_number = %s
              AND tl.line_number = %s
              AND s.surface_type = %s
            LIMIT 1
        """,
            (p_number, line_number, surface),
        ).fetchone()

        if result:
            return (result["id"], confidence)

    # Line number only (may be ambiguous across surfaces)
    results = conn.execute(
        """
        SELECT id FROM text_lines
        WHERE p_number = %s AND line_number = %s
    """,
        (p_number, line_number),
    ).fetchall()

    if len(results) == 1:
        return (results[0]["id"], confidence)
    elif len(results) > 1:
        # Multiple surfaces - lower confidence, pick first
        return (results[0]["id"], confidence * 0.7)

    return (None, 0.0)


def positional_match(
    conn, p_number: str, translation_id: int
) -> tuple[int | None, float]:
    """
    Fallback: match by positional order (translation index → line sequence).

    Returns (line_id, confidence=0.5).
    """
    # Get all translations for this tablet ordered by id
    all_trans = conn.execute(
        """
        SELECT id FROM translations
        WHERE p_number = %s
        ORDER BY id
    """,
        (p_number,),
    ).fetchall()

    # Find position of this translation
    try:
        position = next(i for i, t in enumerate(all_trans) if t["id"] == translation_id)
    except StopIteration:
        return (None, 0.0)

    # NEW: Get total line count for range validation
    line_count = conn.execute(
        """
        SELECT COUNT(*) as cnt FROM text_lines
        WHERE p_number = %s
    """,
        (p_number,),
    ).fetchone()["cnt"]

    # NEW: Validate position is in range
    if position >= line_count:
        # Translation index beyond available lines - no match possible
        return (None, 0.0)

    # Get line at position (now safe - we validated range)
    line = conn.execute(
        """
        SELECT id FROM text_lines
        WHERE p_number = %s
        ORDER BY id
        LIMIT 1 OFFSET %s
    """,
        (p_number, position),
    ).fetchone()

    if line:
        return (line["id"], 0.5)  # Lower confidence for positional

    return (None, 0.0)


def main(args):
    settings = get_settings()

    # Connect to database
    conn = psycopg.connect(
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}",
        row_factory=dict_row,
    )

    # Initialize checkpoint
    checkpoint = ImportCheckpoint("19_translation_matching", reset=args.reset)

    print(f"{'=' * 80}")
    print("STEP 19: Translation Line Matching")
    print(f"{'=' * 80}\n")

    # Get translations without line_id
    total = conn.execute("""
        SELECT COUNT(*) as cnt
        FROM translations
        WHERE line_id IS NULL
    """).fetchone()["cnt"]

    checkpoint.set_total(total)
    print(f"Total translations to match: {total:,}\n")

    # Process in batches using cursor-based pagination
    # Use id > last_processed_id instead of OFFSET to avoid skipping records
    batch_size = 1000
    commit_interval = 5000
    processed_count = 0
    last_processed_id = 0  # Track the max ID we've processed

    unmatched = []
    current_p_number = None

    while True:
        # Fetch batch using cursor (id > last_processed_id)
        translations = conn.execute(
            """
            SELECT id, p_number, translation, line_id
            FROM translations
            WHERE id > %s
            ORDER BY id
            LIMIT %s
        """,
            (last_processed_id, batch_size),
        ).fetchall()

        if not translations:
            break

        for trans in translations:
            # Skip if already matched
            if trans["line_id"] is not None:
                continue

            # Track progress by tablet
            if trans["p_number"] != current_p_number:
                current_p_number = trans["p_number"]
                if processed_count % 1000 == 0:
                    print(f"Processing {current_p_number}...")

            # PHASE 1B: Classify unmatchable translations FIRST
            unmatchable_type = classify_unmatchable(trans["translation"])

            if unmatchable_type:
                # Non-matchable content - record separately, don't try to match
                unmatched.append(
                    {
                        "p_number": trans["p_number"],
                        "translation_id": trans["id"],
                        "text": trans["translation"][:100],
                        "unmatchable_type": unmatchable_type,
                    }
                )
                checkpoint.stats["unmatchable"] = (
                    checkpoint.stats.get("unmatchable", 0) + 1
                )
                continue

            # Extract line info from translation text
            line_info = extract_line_info(trans["translation"])

            if line_info:
                # Try pattern-based match
                line_id, confidence = match_translation_to_line(
                    conn, trans["p_number"], line_info
                )
            else:
                # Fallback to positional match
                line_id, confidence = positional_match(
                    conn, trans["p_number"], trans["id"]
                )

            if line_id:
                conn.execute(
                    """
                    UPDATE translations
                    SET line_id = %s
                    WHERE id = %s
                """,
                    (line_id, trans["id"]),
                )
                checkpoint.stats["updated"] += 1
            else:
                unmatched.append(
                    {
                        "p_number": trans["p_number"],
                        "translation_id": trans["id"],
                        "text": trans["translation"][:100],
                    }
                )
                checkpoint.stats["skipped"] += 1

        checkpoint.stats["processed"] += len(translations)
        processed_count += len(translations)

        # Update cursor for next batch
        if translations:
            last_processed_id = translations[-1]["id"]

        # Periodic commit and progress report
        if processed_count % commit_interval == 0 or checkpoint.interrupted:
            conn.commit()
            checkpoint.save()
            matched_pct = (
                checkpoint.stats["updated"] / checkpoint.stats["processed"] * 100
                if checkpoint.stats["processed"] > 0
                else 0
            )
            print(
                f"Processed {processed_count:,} / {total:,} ({matched_pct:.1f}% matched)"
            )

        if checkpoint.interrupted:
            print("\nInterrupted. Progress saved. Resume with same command.")
            break

        if args.limit and processed_count >= args.limit:
            print(f"\n--limit {args.limit} reached")
            break

    # Final commit
    conn.commit()

    # Mark completion
    if not checkpoint.interrupted and not args.limit:
        checkpoint.save(completed=True)

        # Write unmatched to file for review
        if unmatched:
            progress_dir = Path("_progress")
            progress_dir.mkdir(exist_ok=True)
            unmatched_file = progress_dir / "19_unmatched_translations.json"
            with open(unmatched_file, "w") as f:
                json.dump(unmatched, f, indent=2)
            print(f"\nUnmatched translations exported to {unmatched_file}")

    checkpoint.print_summary()

    # Validation checks
    print(f"\n{'-' * 80}")
    print("VALIDATION")
    print(f"{'-' * 80}")

    result = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN line_id IS NOT NULL THEN 1 ELSE 0 END) as matched,
            ROUND(100.0 * SUM(CASE WHEN line_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) as pct
        FROM translations
    """).fetchone()

    print(f"Total translations: {result['total']:,}")
    print(f"Matched: {result['matched']:,} ({result['pct']}%)")
    print(f"Unmatched: {result['total'] - result['matched']:,}")

    # PHASE 1B: Report on unmatchable classifications
    unmatchable_count = checkpoint.stats.get("unmatchable", 0)
    if unmatchable_count > 0:
        matchable_total = result["total"] - unmatchable_count
        effective_pct = (
            (result["matched"] / matchable_total * 100) if matchable_total > 0 else 0
        )
        print(f"\nUnmatchable (non-line content): {unmatchable_count:,}")
        print(f"Matchable translations: {matchable_total:,}")
        print(
            f"Effective match rate: {result['matched']:,} / {matchable_total:,} ({effective_pct:.1f}%)"
        )

    # Check for orphaned line_ids
    orphans = conn.execute("""
        SELECT COUNT(*) as cnt FROM translations t
        LEFT JOIN text_lines tl ON t.line_id = tl.id
        WHERE t.line_id IS NOT NULL AND tl.id IS NULL
    """).fetchone()
    print(f"\nOrphaned line_ids (referencing non-existent lines): {orphans['cnt']:,}")

    conn.close()

    print(f"\n{'=' * 80}")
    print("STEP 19 COMPLETE")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Match translations to text_lines (Step 19)"
    )
    parser.add_argument(
        "--reset", action="store_true", help="Start fresh, discarding checkpoint"
    )
    parser.add_argument(
        "--limit", type=int, help="Limit number of translations (for testing)"
    )
    args = parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Progress saved.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
