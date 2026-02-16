#!/usr/bin/env python3
"""
Populate Glossary Relationships Table

Creates cross-references between dictionary entries, focusing on:
- Sumerian ↔ Akkadian translation pairs (via guide word matching)
- High-frequency words (icount > 50)

Usage:
    python3 populate_relationships.py

Requirements:
    - Database: ../database/glintstone.db
    - Tables: glossary_entries, glossary_relationships
"""

import sqlite3
from pathlib import Path
from datetime import datetime

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "database" / "glintstone.db"

def populate_sumerian_akkadian_pairs(cursor, min_freq=50, dry_run=False):
    """
    Create translation relationships between Sumerian and Akkadian words
    that share the same guide word (English meaning) and POS.
    """
    print("Finding Sumerian ↔ Akkadian translation pairs...")
    print(f"  Filtering words with frequency >= {min_freq}")
    print()

    # Find matching pairs
    cursor.execute("""
        SELECT
            sux.entry_id as sux_entry,
            sux.headword as sux_word,
            sux.guide_word,
            sux.pos,
            sux.icount as sux_freq,
            akk.entry_id as akk_entry,
            akk.headword as akk_word,
            akk.language as akk_lang,
            akk.icount as akk_freq
        FROM glossary_entries sux
        JOIN glossary_entries akk
          ON sux.guide_word = akk.guide_word
         AND sux.pos = akk.pos
        WHERE sux.language = 'sux'
          AND akk.language LIKE 'akk%'
          AND sux.guide_word IS NOT NULL
          AND sux.guide_word != ''
          AND sux.icount >= ?
        ORDER BY sux.icount DESC, akk.icount DESC
    """, (min_freq,))

    pairs = cursor.fetchall()
    print(f"✓ Found {len(pairs)} potential translation pairs")
    print()

    if dry_run:
        print("Sample pairs (first 10):")
        for i, pair in enumerate(pairs[:10]):
            print(f"  {i+1}. {pair['sux_word']}[{pair['guide_word']}] (sux, {pair['sux_freq']}) "
                  f"↔ {pair['akk_word']} ({pair['akk_lang']}, {pair['akk_freq']})")
        if len(pairs) > 10:
            print(f"  ... and {len(pairs) - 10} more")
        return 0

    # Insert relationships
    inserted = 0
    skipped = 0

    for pair in pairs:
        try:
            # Insert bidirectional relationships
            # Sumerian → Akkadian
            cursor.execute("""
                INSERT OR IGNORE INTO glossary_relationships
                (from_entry_id, to_entry_id, relationship_type, notes, confidence, created_at)
                VALUES (?, ?, 'translation', ?, 'inferred_guidword', ?)
            """, (
                pair['sux_entry'],
                pair['akk_entry'],
                f"Sumerian → Akkadian via guide word '{pair['guide_word']}'",
                datetime.now().isoformat()
            ))

            # Akkadian → Sumerian
            cursor.execute("""
                INSERT OR IGNORE INTO glossary_relationships
                (from_entry_id, to_entry_id, relationship_type, notes, confidence, created_at)
                VALUES (?, ?, 'translation', ?, 'inferred_guidword', ?)
            """, (
                pair['akk_entry'],
                pair['sux_entry'],
                f"Akkadian → Sumerian via guide word '{pair['guide_word']}'",
                datetime.now().isoformat()
            ))

            # Check if actually inserted (IGNORE might have skipped)
            if cursor.rowcount > 0:
                inserted += 2  # Bidirectional
            else:
                skipped += 1

        except sqlite3.IntegrityError as e:
            print(f"  Warning: Could not insert pair {pair['sux_word']} ↔ {pair['akk_word']}: {e}")
            skipped += 1
            continue

    print(f"✓ Inserted {inserted} translation relationships ({inserted // 2} bidirectional pairs)")
    if skipped > 0:
        print(f"  Skipped {skipped} duplicate pairs")

    return inserted


def populate_synonyms(cursor, dry_run=False):
    """
    Create synonym relationships within the same language.
    For now, this is a placeholder - manual curation recommended.
    """
    print("Finding synonyms (within language)...")
    print("  (Skipping - requires manual curation for accuracy)")
    print()
    return 0


def show_statistics(cursor):
    """
    Display statistics about populated relationships.
    """
    print("=" * 60)
    print("Statistics")
    print("=" * 60)

    cursor.execute("SELECT COUNT(*) as total FROM glossary_relationships")
    total = cursor.fetchone()['total']
    print(f"Total relationships: {total}")

    cursor.execute("""
        SELECT relationship_type, COUNT(*) as cnt
        FROM glossary_relationships
        GROUP BY relationship_type
        ORDER BY cnt DESC
    """)
    print("\nBy type:")
    for row in cursor.fetchall():
        print(f"  {row['relationship_type']}: {row['cnt']}")

    cursor.execute("""
        SELECT confidence, COUNT(*) as cnt
        FROM glossary_relationships
        GROUP BY confidence
        ORDER BY cnt DESC
    """)
    print("\nBy confidence:")
    for row in cursor.fetchall():
        print(f"  {row['confidence']}: {row['cnt']}")

    # Sample some relationships
    print("\nSample relationships:")
    cursor.execute("""
        SELECT
            ge1.headword as from_word,
            ge1.guide_word as from_meaning,
            ge1.language as from_lang,
            gr.relationship_type,
            ge2.headword as to_word,
            ge2.guide_word as to_meaning,
            ge2.language as to_lang
        FROM glossary_relationships gr
        JOIN glossary_entries ge1 ON gr.from_entry_id = ge1.entry_id
        JOIN glossary_entries ge2 ON gr.to_entry_id = ge2.entry_id
        ORDER BY RANDOM()
        LIMIT 10
    """)

    for row in cursor.fetchall():
        print(f"  {row['from_word']}[{row['from_meaning']}] ({row['from_lang']}) "
              f"→ {row['to_word']}[{row['to_meaning']}] ({row['to_lang']}) "
              f"[{row['relationship_type']}]")


def populate_relationships(min_freq=50, dry_run=False):
    """
    Main function to populate glossary_relationships table.
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 60)
    print("Glossary Relationships Population Script")
    print("=" * 60)
    print()

    # Clear existing inferred relationships if not dry run
    if not dry_run:
        print("Clearing existing inferred relationships...")
        cursor.execute("""
            DELETE FROM glossary_relationships
            WHERE confidence = 'inferred_guidword'
        """)
        deleted = cursor.rowcount
        print(f"✓ Deleted {deleted} existing inferred relationships")
        print()

    # Populate different relationship types
    total_inserted = 0

    # 1. Sumerian ↔ Akkadian translations
    inserted = populate_sumerian_akkadian_pairs(cursor, min_freq, dry_run)
    total_inserted += inserted

    # 2. Synonyms (placeholder)
    inserted = populate_synonyms(cursor, dry_run)
    total_inserted += inserted

    # Commit changes
    if not dry_run:
        conn.commit()
        print()
        print("✓ Changes committed to database")

    # Show statistics
    print()
    show_statistics(cursor)

    conn.close()
    print()
    print("✓ Complete!")
    print()

    if dry_run:
        print("This was a DRY RUN. No data was written to the database.")
        print("Run without --dry-run to actually populate the table.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Populate glossary relationships")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without writing to database")
    parser.add_argument("--min-freq", type=int, default=50,
                       help="Minimum word frequency (icount) to include (default: 50)")
    args = parser.parse_args()

    populate_relationships(min_freq=args.min_freq, dry_run=args.dry_run)
