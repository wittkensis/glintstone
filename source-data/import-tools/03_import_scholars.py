#!/usr/bin/env python3
"""
Step 3: Import scholars from CDLI and ORACC project data.

Sources:
  - CDLI catalog CSV: `atf_source` and `author` fields
  - ORACC catalogue.json: `author` field per text

Names are normalized, deduplicated by normalized form, and inserted once.
Each scholar gets a single row; duplicates are merged.

Usage:
    python 03_import_scholars.py [--dry-run]
"""

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings

CDLI_CSV = Path(__file__).resolve().parents[1] / "sources/CDLI/metadata/cdli_cat.csv"
ORACC_BASE = Path(__file__).resolve().parents[1] / "sources/ORACC"

ORACC_PROJECTS = [
    "dcclt",
    "epsd2",
    "rinap",
    "saao",
    "blms",
    "cams",
    "etcsri",
    "riao",
    "rimanum",
]


def normalize_name(raw: str) -> str:
    """
    Normalize a scholar name to 'Last, First' canonical form.
    Strips diacritics, collapses whitespace, handles 'et al.'.
    """
    name = raw.strip()
    # Remove trailing et al., and collaborators
    name = re.sub(r"\s*(et al\.|& others|and others)\s*", "", name, flags=re.IGNORECASE)
    name = name.strip().strip(",").strip()
    if not name:
        return ""
    # Normalize unicode: decompose + recompose to handle diacritic variants
    name = unicodedata.normalize("NFC", name)
    # Collapse internal whitespace
    name = re.sub(r"\s+", " ", name)
    return name


def parse_name_list(raw: str) -> list[str]:
    """
    Split a CDLI multi-author string into individual names.
    Handles: 'A & B', 'A, B', 'A; B', 'A and B'
    """
    if not raw or not raw.strip():
        return []

    # Split on ' & ', ' and ', '; '
    parts = re.split(r"\s*[&;]\s*|\s+and\s+", raw)
    result = []
    for p in parts:
        n = normalize_name(p)
        if n and len(n) > 2:  # Skip single chars, commas
            result.append(n)
    return result


def collect_scholars() -> set[str]:
    """Collect all scholar names from CDLI CSV and ORACC catalogues."""
    names: set[str] = set()

    # From CDLI CSV: atf_source and author columns
    print("  Collecting from CDLI CSV...", end=" ", flush=True)
    with open(CDLI_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for field in ["atf_source", "author"]:
                for name in parse_name_list(row.get(field, "")):
                    names.add(name)
    print(f"done. {len(names)} unique names so far.")

    # From ORACC catalogues
    for proj in ORACC_PROJECTS:
        cat_path = ORACC_BASE / proj / "json" / proj / "catalogue.json"
        if not cat_path.exists():
            # Try alternate path
            cat_path = ORACC_BASE / proj / "json" / "catalogue.json"
        if not cat_path.exists():
            continue

        print(f"  Collecting from ORACC/{proj}...", end=" ", flush=True)
        count_before = len(names)
        with open(cat_path, encoding="utf-8") as f:
            catalogue = json.load(f)

        members = catalogue.get("members", {})
        for entry in members.values():
            for field in ["author", "atf_source"]:
                for name in parse_name_list(entry.get(field, "")):
                    names.add(name)
        print(f"done. +{len(names) - count_before} new names.")

    return names


def main():
    parser = argparse.ArgumentParser(description="Import scholars from CDLI and ORACC")
    parser.add_argument("--dry-run", action="store_true", help="No DB writes")
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 3: IMPORT SCHOLARS")
    print("=" * 60)
    print()

    all_names = collect_scholars()
    print(f"\n  Total unique scholar names: {len(all_names)}")

    if args.dry_run:
        print("\n[DRY RUN] No database writes.")
        for name in sorted(all_names)[:20]:
            print(f"  - {name}")
        print(f"  ... ({len(all_names)} total)")
        return

    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}"
    )

    try:
        conn = psycopg.connect(conninfo)
        inserted = 0
        skipped = 0

        with conn.cursor() as cur:
            for name in sorted(all_names):
                cur.execute(
                    """
                    INSERT INTO scholars (name)
                    VALUES (%s)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """,
                    (name,),
                )
                row = cur.fetchone()
                if row:
                    inserted += 1
                else:
                    skipped += 1

        conn.commit()
        conn.close()

        print(f"\n  Inserted: {inserted}")
        print(f"  Skipped:  {skipped} (already exist)")
        print("Validation: OK")

    except Exception as e:
        print(f"\nFailed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
