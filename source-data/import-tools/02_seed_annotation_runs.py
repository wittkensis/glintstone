#!/usr/bin/env python3
"""
Step 2: Create retroactive annotation_run records for all data sources.

Every downstream import row carries an annotation_run_id FK. This step
creates the 13 canonical import run records so downstream scripts can
reference them by source_name.

Idempotent: uses ON CONFLICT DO NOTHING. Safe to re-run.

Usage:
    python 02_seed_annotation_runs.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from psycopg.rows import dict_row

from core.config import get_settings

# Each entry: (source_name, source_type, method, corpus_scope, notes)
ANNOTATION_RUNS = [
    # CDLI bulk data dump (Aug 2022)
    (
        "cdli-catalog",
        "import",
        "import",
        "353,283 artifacts",
        "CDLI bulk data dump (Aug 2022). cdli_cat.csv. CC0.",
    ),
    (
        "cdli-atf",
        "import",
        "import",
        "CDLI ATF transliterations",
        "CDLI bulk ATF dump (Aug 2022). cdliatf_unblocked.atf. CC0.",
    ),
    # CompVis sign annotations (from Heidelberg group)
    (
        "compvis",
        "import",
        "ML_model",
        "81 tablets, ~8,100 sign annotations",
        "Heidelberg CompVis sign detection annotations. CC BY 4.0.",
    ),
    # ORACC projects
    (
        "oracc/dcclt",
        "import",
        "import",
        "Digital Corpus of Cuneiform Lexical Texts",
        "ORACC DCCLT project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/epsd2",
        "import",
        "import",
        "Electronic PSD 2",
        "ORACC ePSD2 Sumerian dictionary corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/rinap",
        "import",
        "import",
        "Royal Inscriptions of the Neo-Assyrian Period",
        "ORACC RINAP project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/saao",
        "import",
        "import",
        "State Archives of Assyria Online",
        "ORACC SAAo project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/blms",
        "import",
        "import",
        "Babylonian Lunar Six Micro Signs",
        "ORACC BLMS project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/cams",
        "import",
        "import",
        "Corpus of Ancient Mesopotamian Scholarship",
        "ORACC CAMS project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/etcsri",
        "import",
        "import",
        "Electronic Text Corpus of Sumerian Royal Inscriptions",
        "ORACC ETCSRI project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/riao",
        "import",
        "import",
        "Royal Inscriptions of Assyria Online",
        "ORACC RIAo project corpus. CC BY-SA 3.0.",
    ),
    (
        "oracc/rimanum",
        "import",
        "import",
        "Rulers of the Ancient Near East",
        "ORACC RImanum project corpus. CC BY-SA 3.0.",
    ),
    # eBL sign annotations
    (
        "ebl-annotations",
        "import",
        "import",
        "eBL sign annotation training data",
        "Electronic Babylonian Library annotation corpus. CC BY 4.0.",
    ),
]


def main():
    parser = argparse.ArgumentParser(description="Seed retroactive annotation_run records")
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing")
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 2: SEED ANNOTATION RUNS")
    print("=" * 60)
    print(f"\n  Records to create: {len(ANNOTATION_RUNS)}")

    if args.dry_run:
        print("\n[DRY RUN] No database writes.")
        for name, src_type, method, scope, notes in ANNOTATION_RUNS:
            print(f"  - {name}")
        return

    settings = get_settings()
    conninfo = (
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}"
    )

    try:
        conn = psycopg.connect(conninfo, row_factory=dict_row)
        inserted = 0
        skipped = 0

        for source_name, source_type, method, corpus_scope, notes in ANNOTATION_RUNS:
            result = conn.execute("""
                INSERT INTO annotation_runs
                    (source_name, source_type, method, corpus_scope, notes)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
            """, (source_name, source_type, method, corpus_scope, notes))
            row = result.fetchone()
            if row:
                print(f"  + {source_name} (id={row['id']})")
                inserted += 1
            else:
                print(f"  . {source_name} (already exists)")
                skipped += 1

        conn.commit()
        conn.close()

        print(f"\nInserted: {inserted}, Skipped: {skipped}")
        assert inserted + skipped == len(ANNOTATION_RUNS)
        print("Validation: OK")

    except Exception as e:
        print(f"\nFailed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
