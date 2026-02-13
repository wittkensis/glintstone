#!/usr/bin/env python3
"""
Backfill OCR status in pipeline_status table.

Sets has_ocr = 1 for all tablets that have ATF transliterations,
treating human transcription as a form of "text recognition".
"""

import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/Volumes/Portable Storage/CUNEIFORM")
DB_PATH = BASE_DIR / "database" / "glintstone.db"


def backfill_ocr_status():
    """Update OCR status based on ATF presence."""
    print("=" * 60)
    print("BACKFILLING OCR STATUS")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get current state
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN has_ocr = 1 THEN 1 ELSE 0 END) as with_ocr,
            SUM(CASE WHEN has_atf = 1 THEN 1 ELSE 0 END) as with_atf
        FROM pipeline_status
    """)
    before = cursor.fetchone()
    print(f"\nBefore:")
    print(f"  Total tablets: {before[0]:,}")
    print(f"  With OCR: {before[1]:,}")
    print(f"  With ATF: {before[2]:,}")

    # Update OCR status for tablets with ATF
    cursor.execute("""
        UPDATE pipeline_status
        SET
            has_ocr = 1,
            ocr_model = 'human_transcription',
            ocr_confidence = 0.95,
            last_updated = CURRENT_TIMESTAMP
        WHERE has_atf = 1 AND has_ocr = 0
    """)
    updated = cursor.rowcount
    print(f"\n  Updated {updated:,} tablets with OCR status")

    # Recalculate quality scores to include OCR
    # New formula: image(20) + ocr(20) + atf(20) + lemmas(20) + translation(20) = 100
    cursor.execute("""
        UPDATE pipeline_status
        SET quality_score = (
            COALESCE(has_image, 0) * 0.20 +
            COALESCE(has_ocr, 0) * 0.20 +
            COALESCE(has_atf, 0) * 0.20 +
            COALESCE(has_lemmas, 0) * 0.20 +
            COALESCE(has_translation, 0) * 0.20
        ),
        last_updated = CURRENT_TIMESTAMP
    """)
    recalculated = cursor.rowcount
    print(f"  Recalculated quality scores for {recalculated:,} tablets")

    conn.commit()

    # Verify results
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN has_ocr = 1 THEN 1 ELSE 0 END) as with_ocr,
            SUM(CASE WHEN has_atf = 1 THEN 1 ELSE 0 END) as with_atf,
            AVG(quality_score) as avg_quality,
            MAX(quality_score) as max_quality
        FROM pipeline_status
    """)
    after = cursor.fetchone()
    print(f"\nAfter:")
    print(f"  Total tablets: {after[0]:,}")
    print(f"  With OCR: {after[1]:,}")
    print(f"  With ATF: {after[2]:,}")
    print(f"  Avg quality score: {after[3]:.2%}")
    print(f"  Max quality score: {after[4]:.2%}")

    # Verify OCR matches ATF
    cursor.execute("""
        SELECT COUNT(*) FROM pipeline_status
        WHERE has_atf = 1 AND has_ocr = 0
    """)
    mismatches = cursor.fetchone()[0]
    if mismatches == 0:
        print(f"\n  All ATF tablets now have OCR status")
    else:
        print(f"\n  WARNING: {mismatches} tablets with ATF still missing OCR status")

    conn.close()

    print("\n" + "=" * 60)
    print(f"COMPLETE: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    backfill_ocr_status()
