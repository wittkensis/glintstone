#!/usr/bin/env python3
"""
Step 23: Import Unicode cuneiform sign metadata into unified lexical schema.

Enriches existing lexical_signs with Unicode code points and official names.
Creates new rows for Unicode signs not already in the database.

Source: ePSD2/unicode/cuneiform-signs.json (1,234 entries)

Usage:
    python 23_import_unicode_signs.py [--dry-run]
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings

UNICODE_FILE = (
    Path(__file__).resolve().parents[1]
    / "sources"
    / "ePSD2"
    / "unicode"
    / "cuneiform-signs.json"
)

SOURCE_NAME = "unicode-standard"
SOURCE_CITATION = "The Unicode Standard, Unicode Consortium"
SOURCE_URL = "https://www.unicode.org/charts/PDF/U12000.pdf"


def parse_sign_name(unicode_name: str) -> str | None:
    """
    Extract a usable sign name from the Unicode character name.
    'CUNEIFORM SIGN A' → 'A'
    'CUNEIFORM SIGN A TIMES BAD' → 'A×BAD'
    'CUNEIFORM NUMERIC SIGN TWO ASH' → None (skip numerics for now)
    'CUNEIFORM PUNCTUATION SIGN OLD ASSYRIAN WORD DIVIDER' → None
    """
    # Only process CUNEIFORM SIGN entries
    m = re.match(r"^CUNEIFORM SIGN (.+)$", unicode_name)
    if not m:
        return None

    raw = m.group(1)
    # Convert 'A TIMES BAD' → 'A×BAD'
    raw = re.sub(r"\s+TIMES\s+", "×", raw)
    # Convert 'A OVER A' → 'A&A'
    raw = re.sub(r"\s+OVER\s+", "&", raw)
    # Convert 'OPPOSING ...' and other multi-word to joined form
    # Keep spaces as they are for multi-word names like 'KA GUNU'
    raw = re.sub(r"\s+OPPOSING\s+", ".OPPOSING.", raw)
    # Simplify 'GUNU' etc (these are modifiers in cuneiform)
    return raw


def main():
    parser = argparse.ArgumentParser(description="Import Unicode cuneiform signs")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 23: IMPORT UNICODE CUNEIFORM SIGNS")
    print(f"  Source: {UNICODE_FILE}")
    print("=" * 60)

    with open(UNICODE_FILE, encoding="utf-8") as f:
        data = json.load(f)

    signs = data.get("signs", [])
    print(f"  Total Unicode entries: {len(signs)}")

    if args.dry_run:
        # Show sample parsing
        for s in signs[:10]:
            parsed = parse_sign_name(s["name"])
            print(f"    {s['name']} → {parsed}  ({s['character']})")
        print("  [DRY RUN] No DB operations.")
        return

    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}"
    )
    conn = psycopg.connect(conninfo)

    stats = {"updated": 0, "inserted": 0, "skipped_numeric": 0, "no_match": 0}

    with conn.cursor() as cur:
        # Index existing signs by unicode_char for matching
        cur.execute(
            "SELECT id, sign_name, unicode_char, source_contributions FROM lexical_signs WHERE unicode_char IS NOT NULL"
        )
        by_unicode = {}
        for sid, name, uc, contributions in cur.fetchall():
            if uc not in by_unicode:
                by_unicode[uc] = {
                    "id": sid,
                    "name": name,
                    "contributions": contributions or {},
                }

        for sign in signs:
            char = sign["character"]
            codepoint = sign["codePoint"]
            name = sign["name"]

            if char in by_unicode:
                # Update existing row with Unicode metadata
                target = by_unicode[char]
                contributions = dict(target["contributions"])
                contributions["unicode_codepoint"] = SOURCE_NAME
                contributions["unicode_name"] = SOURCE_NAME

                cur.execute(
                    """UPDATE lexical_signs
                       SET unicode_codepoint = %s, unicode_name = %s,
                           source_contributions = %s, updated_at = NOW()
                       WHERE id = %s""",
                    (codepoint, name, json.dumps(contributions), target["id"]),
                )
                stats["updated"] += 1
            else:
                # No existing row — try to insert if it's a sign (not numeric/punctuation)
                parsed_name = parse_sign_name(name)
                if not parsed_name:
                    stats["skipped_numeric"] += 1
                    continue

                contributions = {
                    "unicode_char": SOURCE_NAME,
                    "unicode_codepoint": SOURCE_NAME,
                    "unicode_name": SOURCE_NAME,
                }

                cur.execute(
                    """INSERT INTO lexical_signs
                       (sign_name, unicode_char, unicode_codepoint, unicode_name,
                        source, source_citation, source_url, source_contributions)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (sign_name, source) DO NOTHING""",
                    (
                        parsed_name,
                        char,
                        codepoint,
                        name,
                        SOURCE_NAME,
                        SOURCE_CITATION,
                        SOURCE_URL,
                        json.dumps(contributions),
                    ),
                )
                stats["inserted"] += 1

    conn.commit()
    conn.close()

    print(f"\n  Updated existing:     {stats['updated']:,}")
    print(f"  Inserted new:         {stats['inserted']:,}")
    print(f"  Skipped (numeric):    {stats['skipped_numeric']:,}")
    print("Done.")


if __name__ == "__main__":
    main()
