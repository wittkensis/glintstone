#!/usr/bin/env python3
"""
Step 22: Import eBL sign concordance into unified lexical schema.

Merges ABZ numbers and Unicode characters from the eBL sign mapping file
(ebl.txt) into existing lexical_signs rows. Creates new rows only for
signs not already in the database.

Provenance tracked via source_contributions JSONB column.

Source: ebl-annotations/cuneiform_ocr_data/sign_mappings/ebl.txt
Format: SIGN_NAME ABZ_NUMBER UNICODE_CHAR (space-delimited)

Usage:
    python 22_import_ebl_sign_concordance.py [--dry-run]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings

EBL_SIGN_FILE = (
    Path(__file__).resolve().parents[1]
    / "sources"
    / "ebl-annotations"
    / "cuneiform_ocr_data"
    / "sign_mappings"
    / "ebl.txt"
)

SOURCE_NAME = "ebl-sign-list"
SOURCE_CITATION = "Electronic Babylonian Library (eBL), LMU Munich"
SOURCE_URL = "https://www.ebl.lmu.de/"


def parse_ebl_signs(path: Path) -> list[dict]:
    """Parse ebl.txt into a list of sign dicts."""
    signs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 3:
                continue

            sign_name = parts[0]
            abz_raw = parts[1]
            unicode_char = parts[2] if parts[2] != "None" else None

            # Parse ABZ number: "ABZ579" → "579", "NoABZ0" → None
            abz_number = None
            if abz_raw.startswith("ABZ") and not abz_raw.startswith("NoABZ"):
                abz_number = abz_raw[3:]  # Strip "ABZ" prefix

            signs.append(
                {
                    "sign_name": sign_name,
                    "abz_number": abz_number,
                    "unicode_char": unicode_char,
                }
            )
    return signs


def main():
    parser = argparse.ArgumentParser(description="Import eBL sign concordance")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 22: IMPORT eBL SIGN CONCORDANCE")
    print(f"  Source: {EBL_SIGN_FILE}")
    print("=" * 60)

    signs = parse_ebl_signs(EBL_SIGN_FILE)
    print(f"  Parsed {len(signs)} sign entries")
    print(f"  With ABZ number: {sum(1 for s in signs if s['abz_number']):,}")
    print(f"  With Unicode:    {sum(1 for s in signs if s['unicode_char']):,}")

    if args.dry_run:
        print("  [DRY RUN] No DB operations.")
        return

    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}"
    )
    conn = psycopg.connect(conninfo)

    stats = {"merged": 0, "inserted": 0, "skipped": 0}

    with conn.cursor() as cur:
        # Load existing signs indexed by sign_name
        cur.execute(
            "SELECT id, sign_name, sign_number, unicode_char, source, source_contributions FROM lexical_signs"
        )
        existing = {}
        for row in cur.fetchall():
            sid, name, num, uc, source, contributions = row
            if name not in existing:
                existing[name] = []
            existing[name].append(
                {
                    "id": sid,
                    "sign_number": num,
                    "unicode_char": uc,
                    "source": source,
                    "contributions": contributions or {},
                }
            )

        for sign in signs:
            name = sign["sign_name"]
            abz = sign["abz_number"]
            uc = sign["unicode_char"]

            if name in existing:
                # Merge into existing row (prefer first match)
                target = existing[name][0]
                updates = []
                contributions = dict(target["contributions"])

                if abz and not target["sign_number"]:
                    updates.append(("sign_number", abz))
                    contributions["sign_number"] = SOURCE_NAME

                if uc and not target["unicode_char"]:
                    updates.append(("unicode_char", uc))
                    contributions["unicode_char"] = SOURCE_NAME

                if updates:
                    set_clauses = ", ".join(f"{col} = %s" for col, _ in updates)
                    set_clauses += ", source_contributions = %s, updated_at = NOW()"
                    values = [v for _, v in updates] + [
                        json.dumps(contributions),
                        target["id"],
                    ]
                    cur.execute(
                        f"UPDATE lexical_signs SET {set_clauses} WHERE id = %s",
                        values,
                    )
                    stats["merged"] += 1
                else:
                    stats["skipped"] += 1
            else:
                # Insert new sign
                contributions = {}
                if abz:
                    contributions["sign_number"] = SOURCE_NAME
                if uc:
                    contributions["unicode_char"] = SOURCE_NAME

                cur.execute(
                    """INSERT INTO lexical_signs
                       (sign_name, sign_number, unicode_char, source, source_citation,
                        source_url, source_contributions)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (sign_name, source) DO NOTHING""",
                    (
                        name,
                        abz,
                        uc,
                        SOURCE_NAME,
                        SOURCE_CITATION,
                        SOURCE_URL,
                        json.dumps(contributions),
                    ),
                )
                stats["inserted"] += 1

    conn.commit()
    conn.close()

    print(f"\n  Merged into existing: {stats['merged']:,}")
    print(f"  Inserted new:        {stats['inserted']:,}")
    print(f"  Skipped (no change): {stats['skipped']:,}")
    print("Done.")


if __name__ == "__main__":
    main()
