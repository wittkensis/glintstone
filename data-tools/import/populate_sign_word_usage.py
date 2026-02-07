#!/usr/bin/env python3
"""
Populate Sign-Word Usage Table

Analyzes lemmas to determine which cuneiform signs appear in which words,
then populates the sign_word_usage table with usage counts and value types.

Usage:
    python3 populate_sign_word_usage.py

Requirements:
    - Database: ../database/glintstone.db
    - Tables: signs, sign_values, lemmas, glossary_entries
"""

import sqlite3
import re
from pathlib import Path
from collections import defaultdict

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "database" / "glintstone.db"

def parse_sign_from_form(form):
    """
    Extract individual signs from a word form.

    Examples:
        "ka-la-am" → ["ka", "la", "am"]
        "lugal" → ["lugal"]
        "{d}inana" → ["{d}", "inana"]
        "1(disz)" → ["1(disz)"]

    Returns list of (sign_value, is_determinative) tuples
    """
    if not form:
        return []

    form = form.lower().strip()
    signs = []

    # Remove damage markers
    form = re.sub(r'[#?!]+', '', form)

    # Handle determinatives {d}, {f}, {m}, etc.
    det_pattern = r'\{[a-z]+\}'
    for det in re.findall(det_pattern, form):
        signs.append((det, True))

    # Remove determinatives for further processing
    form = re.sub(det_pattern, '', form)

    # Split by hyphens for syllabic signs
    if '-' in form:
        parts = form.split('-')
        for part in parts:
            if part:
                signs.append((part, False))
    # If no hyphens, likely a logogram (single sign)
    elif form:
        signs.append((form, False))

    return signs


def detect_value_type(sign_value, entry):
    """
    Determine if a sign is used logographically, syllabically, or as determinative.

    Heuristics:
    - Determinative: {d}, {f}, {m}, {gi}, etc.
    - Logographic: Full word sign (e.g., LUGAL, KA when = "mouth")
    - Syllabic: Sound value (e.g., ka, la, am in "ka-la-am")
    """
    # Determinatives are marked with curly braces
    if sign_value.startswith('{') and sign_value.endswith('}'):
        return 'determinative'

    # If the citation form equals the sign value, likely logographic
    cf = entry['citation_form'].lower() if entry['citation_form'] else ''
    if sign_value == cf:
        return 'logographic'

    # If multiple signs (hyphenated), individual signs are syllabic
    if '-' in entry['citation_form']:
        return 'syllabic'

    # Default: logographic for single-sign words
    return 'logographic'


def find_sign_id(cursor, sign_value):
    """
    Find sign_id for a given value.
    Try exact match first, then case-insensitive.
    """
    # Try exact match with sign_values table
    cursor.execute("""
        SELECT DISTINCT sign_id
        FROM sign_values
        WHERE LOWER(value) = LOWER(?)
        LIMIT 1
    """, (sign_value.strip('{}'),))  # Strip braces for determinatives

    result = cursor.fetchone()
    if result:
        return result['sign_id']

    # Try matching sign_id directly (for simple signs like "KA", "LUGAL")
    cursor.execute("""
        SELECT sign_id
        FROM signs
        WHERE LOWER(sign_id) = LOWER(?)
        LIMIT 1
    """, (sign_value.upper(),))

    result = cursor.fetchone()
    if result:
        return result['sign_id']

    return None


def populate_sign_word_usage(dry_run=False):
    """
    Main function to populate sign_word_usage table.
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 60)
    print("Sign-Word Usage Population Script")
    print("=" * 60)
    print()

    # Get all glossary entries with their citation forms
    print("Loading glossary entries...")
    cursor.execute("""
        SELECT entry_id, headword, citation_form, language, pos
        FROM glossary_entries
        WHERE citation_form IS NOT NULL
    """)
    entries = cursor.fetchall()
    print(f"✓ Loaded {len(entries)} entries")
    print()

    # Track usage statistics
    usage_map = defaultdict(lambda: {'count': 0, 'sign_id': None, 'value_type': None})
    signs_not_found = set()
    entries_processed = 0

    print("Processing entries...")
    for entry in entries:
        entry_id = entry['entry_id']
        cf = entry['citation_form']

        # Parse signs from citation form
        signs = parse_sign_from_form(cf)

        for sign_value, is_det in signs:
            # Find sign_id
            sign_id = find_sign_id(cursor, sign_value)

            if not sign_id:
                signs_not_found.add(sign_value)
                continue

            # Determine value type
            if is_det:
                value_type = 'determinative'
            else:
                value_type = detect_value_type(sign_value, entry)

            # Create unique key
            key = (sign_id, entry_id, sign_value)

            # Initialize if first time seeing this combination
            if usage_map[key]['sign_id'] is None:
                usage_map[key]['sign_id'] = sign_id
                usage_map[key]['entry_id'] = entry_id
                usage_map[key]['sign_value'] = sign_value
                usage_map[key]['value_type'] = value_type

            # Count occurrences in lemmas
            cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM lemmas
                WHERE cf = ?
                  AND lang = ?
            """, (cf, entry['language']))

            count_result = cursor.fetchone()
            usage_map[key]['count'] = count_result['cnt']

        entries_processed += 1
        if entries_processed % 1000 == 0:
            print(f"  Processed {entries_processed}/{len(entries)} entries...")

    print(f"✓ Processed {entries_processed} entries")
    print(f"✓ Found {len(usage_map)} unique sign-word combinations")
    print()

    if signs_not_found:
        print(f"⚠ Warning: {len(signs_not_found)} sign values not found in database:")
        print(f"  (showing first 20): {list(signs_not_found)[:20]}")
        print()

    # Insert into database
    if dry_run:
        print("DRY RUN: Would insert the following data:")
        for i, (key, data) in enumerate(list(usage_map.items())[:10]):
            print(f"  {data['sign_id']} + {data['entry_id']} → {data['sign_value']} ({data['value_type']}) × {data['count']}")
        if len(usage_map) > 10:
            print(f"  ... and {len(usage_map) - 10} more")
    else:
        print("Inserting into sign_word_usage table...")

        # Clear existing data
        cursor.execute("DELETE FROM sign_word_usage")
        print("  Cleared existing data")

        # Insert new data
        inserted = 0
        for key, data in usage_map.items():
            cursor.execute("""
                INSERT INTO sign_word_usage (sign_id, sign_value, entry_id, usage_count, value_type)
                VALUES (?, ?, ?, ?, ?)
            """, (
                data['sign_id'],
                data['sign_value'],
                data['entry_id'],
                data['count'],
                data['value_type']
            ))
            inserted += 1

            if inserted % 1000 == 0:
                print(f"  Inserted {inserted}/{len(usage_map)} rows...")

        conn.commit()
        print(f"✓ Inserted {inserted} rows")

    # Display statistics
    print()
    print("=" * 60)
    print("Statistics")
    print("=" * 60)

    cursor.execute("SELECT COUNT(*) as total FROM sign_word_usage")
    total = cursor.fetchone()['total']
    print(f"Total sign-word relationships: {total}")

    cursor.execute("SELECT COUNT(DISTINCT sign_id) as cnt FROM sign_word_usage")
    unique_signs = cursor.fetchone()['cnt']
    print(f"Unique signs used: {unique_signs}")

    cursor.execute("SELECT COUNT(DISTINCT entry_id) as cnt FROM sign_word_usage")
    unique_words = cursor.fetchone()['cnt']
    print(f"Unique words: {unique_words}")

    cursor.execute("""
        SELECT value_type, COUNT(*) as cnt
        FROM sign_word_usage
        GROUP BY value_type
        ORDER BY cnt DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row['value_type'] or 'unknown'}: {row['cnt']}")

    conn.close()
    print()
    print("✓ Complete!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Populate sign-word usage table")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without writing to database")
    args = parser.parse_args()

    populate_sign_word_usage(dry_run=args.dry_run)
