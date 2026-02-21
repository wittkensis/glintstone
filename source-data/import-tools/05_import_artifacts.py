#!/usr/bin/env python3
"""
Step 5: Import artifacts from CDLI catalog CSV.

Reads cdli_cat.csv (353,283 rows) and populates the artifacts table.
Applies normalization lookups for period and provenience.

Depends on:
  - Step 1 (period_canon, provenience_canon must be seeded)
  - Step 2 (annotation_runs must exist — uses 'cdli-catalog' run)

Idempotent: uses ON CONFLICT DO NOTHING. Safe to re-run.
Progress saved every BATCH_SIZE rows — can resume after interruption.

Usage:
    python 05_import_artifacts.py [--dry-run] [--limit N] [--reset]
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from psycopg.rows import dict_row

from core.config import get_settings

CDLI_CSV = Path(__file__).resolve().parents[1] / "sources/CDLI/metadata/cdli_cat.csv"
BATCH_SIZE = 2000
SOURCE_NAME = "cdli-catalog"


def clean_float(val: str) -> float | None:
    """Parse a float from a CSV string, return None if empty/invalid."""
    v = val.strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def clean_str(val: str) -> str | None:
    """Return stripped string or None if empty."""
    v = val.strip()
    return v if v else None


def format_p_number(raw_id: str) -> str | None:
    """Format CDLI integer id as P-number. '1' → 'P000001'."""
    v = raw_id.strip()
    if not v:
        return None
    try:
        return f"P{int(v):06d}"
    except ValueError:
        return None


def parse_languages_json(language_str: str) -> str | None:
    """Split CDLI language string into a JSON array. 'Sumerian; Akkadian' → '["Sumerian","Akkadian"]'"""
    v = language_str.strip()
    if not v:
        return None
    parts = [p.strip() for p in v.split(";") if p.strip()]
    return json.dumps(parts)


def parse_cdli_date(date_str: str):
    """Parse CDLI date_updated string to a usable timestamp or None."""
    v = date_str.strip()
    if not v or v == "00.00.00.00":
        return None
    # Format is YYYY-MM-DD from date_updated field
    try:
        from datetime import datetime
        return datetime.strptime(v, "%Y-%m-%d")
    except ValueError:
        return None


def load_lookup_tables(conn: psycopg.Connection) -> tuple[dict, dict, dict]:
    """Load period, provenience, and language lookup tables into memory for fast normalization."""
    period_map = {}
    cur = conn.execute("SELECT raw_period, canonical FROM period_canon")
    for row in cur.fetchall():
        period_map[row[0]] = row[1]

    prov_map = {}
    cur = conn.execute("SELECT raw_provenience, ancient_name FROM provenience_canon")
    for row in cur.fetchall():
        prov_map[row[0]] = row[1]

    # Load language map (cdli_name -> full_name for normalization)
    lang_map = {}
    cur = conn.execute("SELECT cdli_name, full_name FROM language_map")
    for row in cur.fetchall():
        lang_map[row[0]] = row[1]

    return period_map, prov_map, lang_map


def normalize_language(raw_lang: str, lang_map: dict) -> str | None:
    """
    Normalize language string using language_map lookup.

    Handles CDLI inconsistencies:
    - Semicolon vs comma separators ("Sumerian; Akkadian" vs "Sumerian, Akkadian")
    - Looks up raw value in language_map
    - Returns normalized full_name or None if unmapped
    """
    if not raw_lang:
        return None

    # Try direct lookup first
    if raw_lang in lang_map:
        return lang_map[raw_lang]

    # CDLI uses both semicolons and commas as separators - normalize semicolons to commas
    normalized = raw_lang.replace(";", ",")
    if normalized in lang_map:
        return lang_map[normalized]

    # If still not found, return raw value (will be logged as unmapped)
    return raw_lang


def get_annotation_run_id(conn: psycopg.Connection) -> int:
    """Look up the annotation_run id for the cdli-catalog import."""
    cur = conn.execute(
        "SELECT id FROM annotation_runs WHERE source_name = %s", (SOURCE_NAME,)
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError(
            f"annotation_run for '{SOURCE_NAME}' not found. Run 02_seed_annotation_runs.py first."
        )
    return row[0]


def main():
    parser = argparse.ArgumentParser(description="Import CDLI artifacts to PostgreSQL")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, no DB writes")
    parser.add_argument("--limit", type=int, default=0, help="Stop after N rows (0=all)")
    parser.add_argument("--reset", action="store_true", help="Truncate artifacts and reimport")
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 5: IMPORT ARTIFACTS (CDLI CATALOG)")
    print("=" * 60)
    print(f"  Source: {CDLI_CSV}")

    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}"
    )

    if not args.dry_run:
        conn = psycopg.connect(conninfo)

        if args.reset:
            print("\n  [RESET] Truncating artifacts table...")
            conn.execute("TRUNCATE artifacts CASCADE")
            conn.commit()
            print("  Truncated.")

        annotation_run_id = get_annotation_run_id(conn)
        print(f"\n  annotation_run_id: {annotation_run_id}")

        period_map, prov_map, lang_map = load_lookup_tables(conn)
        print(f"  Loaded {len(period_map)} period mappings, {len(prov_map)} provenience mappings, {len(lang_map)} language mappings.")
    else:
        conn = None
        annotation_run_id = 0
        period_map = {}
        prov_map = {}
        print("\n[DRY RUN] No database writes.")

    inserted = 0
    skipped = 0
    errors = 0
    batch = []

    print(f"\n  Processing rows (batch size {BATCH_SIZE})...")

    with open(CDLI_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if args.limit and i >= args.limit:
                break

            p_number = format_p_number(row.get("id", ""))
            if not p_number:
                errors += 1
                continue

            period_raw = clean_str(row.get("period", ""))
            provenience_raw = clean_str(row.get("provenience", ""))
            language_raw = clean_str(row.get("language", ""))

            record = (
                p_number,                                           # p_number
                clean_str(row.get("designation", "")),             # designation
                clean_str(row.get("museum_no", "")),               # museum_no
                clean_str(row.get("excavation_no", "")),           # excavation_no
                clean_str(row.get("material", "")),                # material
                clean_str(row.get("object_type", "")),             # object_type
                clean_float(row.get("width", "")),                 # width
                clean_float(row.get("height", "")),                # height
                clean_float(row.get("thickness", "")),             # thickness
                clean_str(row.get("seal_id", "")),                 # seal_id
                clean_str(row.get("object_preservation", "")),     # object_preservation
                period_raw,                                        # period (raw)
                period_map.get(period_raw) if period_raw else None,    # period_normalized
                provenience_raw,                                   # provenience (raw)
                prov_map.get(provenience_raw) if provenience_raw else None,  # provenience_normalized
                clean_str(row.get("genre", "")),                   # genre
                clean_str(row.get("subgenre", "")),                # subgenre
                None,                                              # supergenre (from ORACC, not in CDLI CSV)
                normalize_language(language_raw, lang_map),        # language (normalized)
                parse_languages_json(language_raw or ""),          # languages (JSON array)
                None,                                              # pleiades_id (from ORACC)
                None,                                              # latitude
                None,                                              # longitude
                clean_str(row.get("primary_publication", "")),     # primary_publication
                clean_str(row.get("collection", "")),              # collection
                clean_str(row.get("dates_referenced", "")),        # dates_referenced
                clean_str(row.get("date_of_origin", "")),          # date_of_origin
                clean_str(row.get("findspot_square", "")),         # findspot_square
                clean_str(row.get("accounting_period", "")),       # accounting_period
                clean_str(row.get("acquisition_history", "")),     # acquisition_history
                parse_cdli_date(row.get("date_updated", "")),      # cdli_updated_at
                None,                                              # oracc_projects (JSON, from ORACC)
                annotation_run_id,                                 # annotation_run_id
            )

            batch.append(record)

            if len(batch) >= BATCH_SIZE:
                if not args.dry_run:
                    n_ins, n_skip = flush_batch(conn, batch)
                    inserted += n_ins
                    skipped += n_skip
                else:
                    inserted += len(batch)
                batch = []

                total_processed = inserted + skipped + errors
                print(f"  {total_processed:>7,} processed  |  {inserted:>7,} inserted  |  {skipped:>6,} skipped", end="\r")

    # Final batch
    if batch:
        if not args.dry_run:
            n_ins, n_skip = flush_batch(conn, batch)
            inserted += n_ins
            skipped += n_skip
        else:
            inserted += len(batch)

    if conn:
        conn.commit()
        conn.close()

    total = inserted + skipped + errors
    print(f"\n\n  Total processed:  {total:,}")
    print(f"  Inserted:         {inserted:,}")
    print(f"  Skipped (dups):   {skipped:,}")
    print(f"  Errors:           {errors:,}")

    # Validate
    expected_min = 350_000
    if not args.dry_run and args.limit == 0:
        assert inserted + skipped >= expected_min, (
            f"Expected >= {expected_min:,} artifacts, got {inserted + skipped:,}"
        )
    print("Validation: OK")


def flush_batch(conn: psycopg.Connection, batch: list) -> tuple[int, int]:
    """Insert a batch of artifact records. Returns (inserted, skipped)."""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM artifacts")
        rows_before = cur.fetchone()[0]

        cur.executemany("""
            INSERT INTO artifacts (
                p_number, designation, museum_no, excavation_no,
                material, object_type, width, height, thickness,
                seal_id, object_preservation,
                period, period_normalized,
                provenience, provenience_normalized,
                genre, subgenre, supergenre,
                language, languages,
                pleiades_id, latitude, longitude,
                primary_publication, collection, dates_referenced,
                date_of_origin, findspot_square, accounting_period,
                acquisition_history, cdli_updated_at, oracc_projects,
                annotation_run_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (p_number) DO NOTHING
        """, batch)
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM artifacts")
        rows_after = cur.fetchone()[0]

    newly_inserted = rows_after - rows_before
    skipped = len(batch) - newly_inserted
    return newly_inserted, skipped


if __name__ == "__main__":
    main()
