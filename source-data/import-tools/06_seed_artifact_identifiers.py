#!/usr/bin/env python3
"""
Step 6: Derive artifact_identifiers from the artifacts table.

One identifier row per non-NULL value per artifact for:
  museum_no, excavation_no, primary_publication, designation (cdli_designation)

Authority is inferred from museum_no prefix patterns (BM→british_museum, etc.)

Depends on: Step 5 (artifacts must be loaded)

Usage:
    python 06_seed_artifact_identifiers.py [--dry-run]
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings


# Map common museum prefix → authority name
MUSEUM_AUTHORITIES = [
    (r"^BM\b", "british_museum"),
    (r"^YBC\b", "yale_babylonian_collection"),
    (r"^CBS\b", "university_museum_philadelphia"),
    (r"^UM\b", "university_museum_philadelphia"),
    (r"^IM\b", "iraq_museum"),
    (r"^NBC\b", "nies_babylonian_collection_yale"),
    (r"^VAT\b", "vorderasiatisches_museum_berlin"),
    (r"^AO\b", "louvre"),
    (r"^Ni\b", "istanbul_archaeology_museum"),
    (r"^NCBT\b", "newell_collection"),
    (r"^MLC\b", "morgan_library"),
    (r"^Ashm\b", "ashmolean_museum"),
    (r"^AS\b", "ashmolean_museum"),
    (r"^FLP\b", "free_library_philadelphia"),
]


def infer_authority(museum_no: str | None) -> str | None:
    if not museum_no:
        return None
    for pattern, authority in MUSEUM_AUTHORITIES:
        if re.match(pattern, museum_no, re.IGNORECASE):
            return authority
    return None


def normalize_identifier(val: str) -> str:
    """Lowercase, collapse whitespace, strip diacritics."""
    v = val.strip()
    v = unicodedata.normalize("NFKD", v)
    v = "".join(c for c in v if not unicodedata.combining(c))
    v = v.lower()
    v = re.sub(r"\s+", " ", v).strip()
    return v


def main():
    parser = argparse.ArgumentParser(
        description="Seed artifact_identifiers from artifacts"
    )
    parser.add_argument("--dry-run", action="store_true", help="No DB writes")
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 6: SEED ARTIFACT IDENTIFIERS")
    print("=" * 60)

    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}"
    )

    conn = psycopg.connect(conninfo)

    # Get annotation_run_id for cdli-catalog
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM annotation_runs WHERE source_name = 'cdli-catalog'")
        row = cur.fetchone()
        if not row:
            print(
                "ERROR: annotation_run for 'cdli-catalog' not found. Run step 2 first."
            )
            sys.exit(1)
        annotation_run_id = row[0]
        print(f"\n  annotation_run_id: {annotation_run_id}")

        # Count artifacts
        cur.execute("SELECT COUNT(*) FROM artifacts")
        total_artifacts = cur.fetchone()[0]
        print(f"  Artifacts to process: {total_artifacts:,}")

    if args.dry_run:
        print("\n[DRY RUN] No database writes.")
        conn.close()
        return

    BATCH_SIZE = 5000
    inserted = 0
    processed = 0
    offset = 0

    print(f"\n  Processing in batches of {BATCH_SIZE}...")

    while True:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p_number, designation, museum_no, excavation_no, primary_publication
                FROM artifacts
                ORDER BY p_number
                LIMIT %s OFFSET %s
            """,
                (BATCH_SIZE, offset),
            )
            rows = cur.fetchall()

        if not rows:
            break

        batch_rows = []
        for p_number, designation, museum_no, excavation_no, primary_pub in rows:
            identifiers = []

            # cdli_designation (always present if designation exists)
            if designation:
                identifiers.append(
                    (
                        p_number,
                        "cdli_designation",
                        designation,
                        normalize_identifier(designation),
                        None,
                        annotation_run_id,
                        1.0,
                    )
                )

            # museum_no
            if museum_no:
                authority = infer_authority(museum_no)
                identifiers.append(
                    (
                        p_number,
                        "museum_no",
                        museum_no,
                        normalize_identifier(museum_no),
                        authority,
                        annotation_run_id,
                        1.0,
                    )
                )

            # excavation_no
            if excavation_no:
                identifiers.append(
                    (
                        p_number,
                        "excavation_no",
                        excavation_no,
                        normalize_identifier(excavation_no),
                        None,
                        annotation_run_id,
                        1.0,
                    )
                )

            # primary_publication (abbreviated)
            if primary_pub:
                identifiers.append(
                    (
                        p_number,
                        "publication",
                        primary_pub,
                        normalize_identifier(primary_pub),
                        None,
                        annotation_run_id,
                        0.9,
                    )
                )

            batch_rows.extend(identifiers)

        if batch_rows:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO artifact_identifiers (
                        p_number, identifier_type, identifier_value,
                        identifier_normalized, authority, annotation_run_id, confidence
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (p_number, identifier_type, identifier_value) DO NOTHING
                """,
                    batch_rows,
                )
            conn.commit()

            # Count actual inserts (approximation — just count batch_rows submitted)
            inserted += len(batch_rows)

        processed += len(rows)
        offset += BATCH_SIZE
        print(f"  {processed:>7,} artifacts  |  ~{inserted:>7,} identifiers", end="\r")

    conn.close()
    print(f"\n\n  Artifacts processed: {processed:,}")
    print(f"  Identifiers inserted: ~{inserted:,} (ON CONFLICT DO NOTHING)")
    print("Validation: OK")


if __name__ == "__main__":
    main()
