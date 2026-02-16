#!/usr/bin/env python3
"""
Import CAD extraction results into glintstone.db.

Usage:
    python import_cad_entries.py output/cad_all.jsonl
    python import_cad_entries.py --all
    python import_cad_entries.py --reset  # Clear and reimport

This script:
1. Reads JSONL extraction output
2. Normalizes and validates entries
3. Imports into cad_* tables in glintstone.db
4. Resolves cross-references between entries
5. Builds full-text search index
"""

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional


def normalize_headword(headword: str) -> str:
    """
    Normalize headword for search.

    Removes diacritics and converts to lowercase.
    """
    # Decompose unicode characters
    nfkd = unicodedata.normalize('NFKD', headword)
    # Remove combining characters (diacritics)
    ascii_text = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return ascii_text.lower()


def extract_volume_from_path(filepath: Path) -> str:
    """Extract volume ID from filename like cad_a1.jsonl."""
    name = filepath.stem
    if name.startswith("cad_"):
        return name[4:].upper()  # "a1" -> "A1"
    return name.upper()


def parse_jsonl_file(filepath: Path) -> List[dict]:
    """Parse a JSONL file into a list of entries."""
    entries = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError as e:
                print(f"  Warning: Invalid JSON on line {line_num}: {e}")
    return entries


def create_tables(conn: sqlite3.Connection):
    """Create CAD tables if they don't exist."""
    script_dir = Path(__file__).parent.parent.parent.parent
    migration_path = script_dir / "database" / "migrations" / "add_cad_tables.sql"

    if migration_path.exists():
        print(f"  Running migration: {migration_path.name}")
        with open(migration_path, 'r') as f:
            conn.executescript(f.read())
    else:
        print(f"  Warning: Migration file not found: {migration_path}")
        # Create minimal tables inline
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS cad_entries (
                id INTEGER PRIMARY KEY,
                headword TEXT NOT NULL,
                headword_normalized TEXT,
                part_of_speech TEXT,
                volume TEXT NOT NULL,
                page_start INTEGER,
                page_end INTEGER,
                raw_text TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS cad_meanings (
                id INTEGER PRIMARY KEY,
                entry_id INTEGER REFERENCES cad_entries(id),
                position TEXT,
                definition TEXT,
                semantic_domain TEXT,
                context TEXT
            );

            CREATE TABLE IF NOT EXISTS cad_attestations (
                id INTEGER PRIMARY KEY,
                entry_id INTEGER REFERENCES cad_entries(id),
                meaning_id INTEGER,
                text_reference TEXT,
                akkadian_text TEXT,
                translation TEXT,
                period TEXT
            );

            CREATE TABLE IF NOT EXISTS cad_cross_references (
                id INTEGER PRIMARY KEY,
                from_entry_id INTEGER REFERENCES cad_entries(id),
                to_headword TEXT,
                to_entry_id INTEGER,
                reference_type TEXT
            );

            CREATE TABLE IF NOT EXISTS cad_logograms (
                id INTEGER PRIMARY KEY,
                entry_id INTEGER REFERENCES cad_entries(id),
                sumerian_form TEXT,
                pronunciation TEXT,
                context TEXT
            );
        """)


def clear_tables(conn: sqlite3.Connection):
    """Clear all CAD tables."""
    print("  Clearing existing CAD data...")
    conn.execute("DELETE FROM cad_logograms")
    conn.execute("DELETE FROM cad_cross_references")
    conn.execute("DELETE FROM cad_attestations")
    conn.execute("DELETE FROM cad_meanings")
    conn.execute("DELETE FROM cad_entries")
    conn.commit()


def import_entry(conn: sqlite3.Connection, entry: dict, volume: str) -> int:
    """
    Import a single entry and return its ID.
    """
    headword = entry.get("headword", "")
    if not headword:
        return 0

    # Insert entry
    cursor = conn.execute("""
        INSERT INTO cad_entries (headword, headword_normalized, part_of_speech, volume, raw_text)
        VALUES (?, ?, ?, ?, ?)
    """, (
        headword,
        normalize_headword(headword),
        entry.get("part_of_speech"),
        volume,
        json.dumps(entry, ensure_ascii=False),
    ))
    entry_id = cursor.lastrowid

    # Insert meanings
    for meaning in entry.get("meanings", []):
        cursor = conn.execute("""
            INSERT INTO cad_meanings (entry_id, position, definition, semantic_domain, context)
            VALUES (?, ?, ?, ?, ?)
        """, (
            entry_id,
            meaning.get("position"),
            meaning.get("definition"),
            meaning.get("semantic_domain"),
            meaning.get("context"),
        ))
        meaning_id = cursor.lastrowid

        # Insert attestations for this meaning
        for attestation in meaning.get("attestations", []):
            conn.execute("""
                INSERT INTO cad_attestations
                (entry_id, meaning_id, text_reference, akkadian_text, translation, period)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                entry_id,
                meaning_id,
                attestation.get("text_reference"),
                attestation.get("akkadian_text"),
                attestation.get("translation"),
                attestation.get("period"),
            ))

    # Insert logograms
    for logogram in entry.get("logograms", []):
        conn.execute("""
            INSERT INTO cad_logograms (entry_id, sumerian_form, pronunciation, context)
            VALUES (?, ?, ?, ?)
        """, (
            entry_id,
            logogram.get("sumerian_form"),
            logogram.get("pronunciation"),
            logogram.get("context"),
        ))

    # Insert cross-references
    for xref in entry.get("cross_references", []):
        conn.execute("""
            INSERT INTO cad_cross_references (from_entry_id, to_headword, reference_type)
            VALUES (?, ?, ?)
        """, (
            entry_id,
            xref.get("to_headword"),
            xref.get("reference_type"),
        ))

    return entry_id


def resolve_cross_references(conn: sqlite3.Connection):
    """Resolve cross-reference links to actual entry IDs."""
    print("  Resolving cross-references...")

    # Update cross-references where we can find the target entry
    conn.execute("""
        UPDATE cad_cross_references
        SET to_entry_id = (
            SELECT id FROM cad_entries
            WHERE headword = cad_cross_references.to_headword
            OR headword_normalized = LOWER(cad_cross_references.to_headword)
            LIMIT 1
        )
        WHERE to_entry_id IS NULL
    """)

    # Count resolved vs unresolved
    cursor = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN to_entry_id IS NOT NULL THEN 1 ELSE 0 END) as resolved
        FROM cad_cross_references
    """)
    row = cursor.fetchone()
    print(f"    Resolved: {row[1]}/{row[0]} cross-references")


def build_fts_index(conn: sqlite3.Connection):
    """Rebuild the full-text search index."""
    print("  Building FTS index...")

    # Clear existing FTS data
    try:
        conn.execute("DELETE FROM cad_fts")
    except sqlite3.OperationalError:
        pass  # Table might not exist

    # Rebuild FTS index
    try:
        conn.execute("""
            INSERT INTO cad_fts (rowid, headword, definition, akkadian_text, translation)
            SELECT
                e.id,
                e.headword,
                GROUP_CONCAT(m.definition, '; '),
                GROUP_CONCAT(a.akkadian_text, ' '),
                GROUP_CONCAT(a.translation, ' ')
            FROM cad_entries e
            LEFT JOIN cad_meanings m ON m.entry_id = e.id
            LEFT JOIN cad_attestations a ON a.entry_id = e.id
            GROUP BY e.id
        """)
    except sqlite3.OperationalError as e:
        print(f"    Warning: Could not build FTS index: {e}")


def main():
    parser = argparse.ArgumentParser(description="Import CAD entries to glintstone.db")
    parser.add_argument("files", nargs="*", help="JSONL files to import")
    parser.add_argument("--all", "-a", action="store_true", help="Import all output/*.jsonl files")
    parser.add_argument("--reset", "-r", action="store_true", help="Clear existing data first")
    parser.add_argument("--db", help="Database path (default: auto-detect)")
    args = parser.parse_args()

    # Find database
    script_dir = Path(__file__).parent.parent
    if args.db:
        db_path = Path(args.db)
    else:
        # Try to find glintstone.db
        candidates = [
            script_dir.parent.parent / "database" / "glintstone.db",
            script_dir / "database" / "glintstone.db",
            Path("database/glintstone.db"),
        ]
        db_path = None
        for candidate in candidates:
            if candidate.exists():
                db_path = candidate
                break
        if not db_path:
            print("ERROR: Could not find glintstone.db")
            print("Specify path with --db option")
            return 1

    # Find input files
    if args.all:
        output_dir = script_dir / "output"
        files = sorted(output_dir.glob("cad_*.jsonl"))
        # Exclude the merged file if individual files exist
        if len(files) > 1:
            files = [f for f in files if f.stem != "cad_all"]
    elif args.files:
        files = [Path(f) for f in args.files]
    else:
        parser.print_help()
        return 1

    if not files:
        print("ERROR: No input files found")
        return 1

    print("=" * 60)
    print("CAD DATABASE IMPORT")
    print("=" * 60)
    print(f"Database: {db_path}")
    print(f"Files: {len(files)}")
    print()

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Create tables
    print("[Step 1] Ensuring tables exist...")
    create_tables(conn)

    # Reset if requested
    if args.reset:
        print("[Step 2] Clearing existing data...")
        clear_tables(conn)
    else:
        print("[Step 2] Keeping existing data (use --reset to clear)")

    # Import files
    print("[Step 3] Importing entries...")
    total_entries = 0
    total_meanings = 0

    for filepath in files:
        if not filepath.exists():
            print(f"  Warning: File not found: {filepath}")
            continue

        volume = extract_volume_from_path(filepath)
        entries = parse_jsonl_file(filepath)

        print(f"  {filepath.name}: {len(entries)} entries")

        for entry in entries:
            entry_id = import_entry(conn, entry, volume)
            if entry_id:
                total_entries += 1
                total_meanings += len(entry.get("meanings", []))

        conn.commit()

    # Resolve cross-references
    print("[Step 4] Post-processing...")
    resolve_cross_references(conn)
    build_fts_index(conn)
    conn.commit()

    # Summary stats
    print()
    print("=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)

    cursor = conn.execute("SELECT COUNT(*) FROM cad_entries")
    entry_count = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM cad_meanings")
    meaning_count = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM cad_attestations")
    attestation_count = cursor.fetchone()[0]

    print(f"  Entries: {entry_count}")
    print(f"  Meanings: {meaning_count}")
    print(f"  Attestations: {attestation_count}")

    conn.close()
    print()
    print("Next step: ./05_verify.sh")

    return 0


if __name__ == "__main__":
    sys.exit(main())
