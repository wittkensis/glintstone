#!/usr/bin/env python3
"""
Cleanup and Re-import ePSD2 Data

This script:
1. Runs cleanup SQL (removes duplicates + old associations)
2. Re-runs import with revised schema (single values array + case-insensitive)
3. Verifies results

Usage:
    python 15c_cleanup_and_reimport.py
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings

CLEANUP_SQL = Path(__file__).parent / "15b_cleanup_duplicates.sql"
IMPORT_SCRIPT = Path(__file__).parent / "15_import_epsd2_unified.py"


def run_cleanup(conn: psycopg.Connection):
    """Run cleanup SQL script."""
    print("\n" + "=" * 80)
    print("STEP 1: Cleanup Duplicate Data")
    print("=" * 80 + "\n")

    if not CLEANUP_SQL.exists():
        print(f"⚠ Cleanup SQL not found: {CLEANUP_SQL}")
        return False

    with open(CLEANUP_SQL, "r") as f:
        cleanup_sql = f.read()

    try:
        # Execute cleanup
        conn.execute(cleanup_sql)
        conn.commit()
        print("✓ Cleanup complete\n")
        return True
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")
        conn.rollback()
        return False


def run_import():
    """Run import script."""
    print("\n" + "=" * 80)
    print("STEP 2: Re-import with Revised Schema")
    print("=" * 80 + "\n")

    if not IMPORT_SCRIPT.exists():
        print(f"⚠ Import script not found: {IMPORT_SCRIPT}")
        return False

    try:
        # Run import script
        subprocess.run(
            [sys.executable, str(IMPORT_SCRIPT)],
            check=True,
            capture_output=False,
        )
        print("\n✓ Import complete\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Import failed: {e}")
        return False


def verify_results(conn: psycopg.Connection):
    """Verify cleanup and import results."""
    print("\n" + "=" * 80)
    print("STEP 3: Verification")
    print("=" * 80 + "\n")

    # Count signs
    sign_count = conn.execute(
        "SELECT COUNT(*) FROM lexical_signs WHERE source = 'epsd2-sl'"
    ).fetchone()[0]

    # Count unique sign names
    unique_signs = conn.execute(
        "SELECT COUNT(DISTINCT sign_name) FROM lexical_signs WHERE source = 'epsd2-sl'"
    ).fetchone()[0]

    # Count associations
    assoc_count = conn.execute(
        "SELECT COUNT(*) FROM lexical_sign_lemma_associations WHERE source = 'epsd2-sl'"
    ).fetchone()[0]

    # Count lemmas
    lemma_count = conn.execute(
        "SELECT COUNT(*) FROM lexical_lemmas WHERE source = 'epsd2'"
    ).fetchone()[0]

    # Count senses
    sense_count = conn.execute(
        "SELECT COUNT(*) FROM lexical_senses WHERE source = 'epsd2'"
    ).fetchone()[0]

    print(f"Signs (total):           {sign_count:,}")
    print(f"Signs (unique names):    {unique_signs:,}")
    print(f"Sign-Lemma associations: {assoc_count:,}")
    print(f"Lemmas:                  {lemma_count:,}")
    print(f"Senses:                  {sense_count:,}")

    # Expected results
    print("\n" + "-" * 80)
    print("Expected vs Actual:")
    print("-" * 80)
    print(f"Signs should be:         2,093 (actual: {unique_signs:,})")
    print(
        f"Associations should be:  ~2,725 (actual: {assoc_count:,}) [+400 from case-insensitive]"
    )

    if unique_signs == sign_count == 2093:
        print("\n✓ No duplicates - idempotency working!")
    elif unique_signs == 2093 and sign_count > 2093:
        print(f"\n⚠ Warning: {sign_count - 2093} duplicate entries still exist")
    else:
        print(f"\n⚠ Warning: Expected 2,093 unique signs, got {unique_signs}")

    if assoc_count > 2325:
        improvement = assoc_count - 2325
        print(
            f"✓ Association improvement: +{improvement} from case-insensitive matching"
        )
    else:
        print(
            f"⚠ Warning: Associations did not increase (expected ~2,725, got {assoc_count:,})"
        )


def main():
    settings = get_settings()

    # Connect to database
    conn = psycopg.connect(
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}",
        row_factory=psycopg.rows.dict_row,
    )

    print("\n" + "=" * 80)
    print("ePSD2 CLEANUP & RE-IMPORT")
    print("=" * 80)

    # Step 1: Cleanup
    if not run_cleanup(conn):
        print("\n✗ Failed at cleanup step")
        return 1

    # Step 2: Import
    if not run_import():
        print("\n✗ Failed at import step")
        return 1

    # Step 3: Verify
    verify_results(conn)

    print("\n" + "=" * 80)
    print("COMPLETE")
    print("=" * 80 + "\n")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
