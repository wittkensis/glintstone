#!/usr/bin/env python3
"""
Full Fix: Alter Schema + Cleanup + Re-import ePSD2 Data

This script runs the complete fix for Phase 3:
1. Alter table schema (single values array + unique constraint)
2. Cleanup duplicates and old associations
3. Re-import with revised logic (case-insensitive matching + subscript normalization)
4. Verify results

Usage:
    python 15d_run_full_fix.py
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from core.config import get_settings

ALTER_SQL = Path(__file__).parents[1] / "migrations/008a_alter_to_single_values.sql"
CLEANUP_SQL = Path(__file__).parent / "15b_cleanup_duplicates.sql"
IMPORT_SCRIPT = Path(__file__).parent / "15_import_epsd2_unified.py"


def run_alter_migration(conn: psycopg.Connection):
    """Run ALTER migration to update schema."""
    print("\n" + "=" * 80)
    print("STEP 1: Alter Table Schema")
    print("=" * 80 + "\n")

    if not ALTER_SQL.exists():
        print(f"⚠ ALTER SQL not found: {ALTER_SQL}")
        return False

    with open(ALTER_SQL, "r") as f:
        alter_sql = f.read()

    try:
        conn.execute(alter_sql)
        conn.commit()
        print("✓ Schema alteration complete\n")
        return True
    except Exception as e:
        print(f"✗ Schema alteration failed: {e}")
        conn.rollback()
        return False


def run_cleanup(conn: psycopg.Connection):
    """Run cleanup SQL script."""
    print("\n" + "=" * 80)
    print("STEP 2: Cleanup Duplicate Data")
    print("=" * 80 + "\n")

    if not CLEANUP_SQL.exists():
        print(f"⚠ Cleanup SQL not found: {CLEANUP_SQL}")
        return False

    with open(CLEANUP_SQL, "r") as f:
        cleanup_sql = f.read()

    try:
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
    print("STEP 3: Re-import with Revised Logic")
    print("=" * 80 + "\n")

    if not IMPORT_SCRIPT.exists():
        print(f"⚠ Import script not found: {IMPORT_SCRIPT}")
        return False

    try:
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
    """Verify all steps completed successfully."""
    print("\n" + "=" * 80)
    print("STEP 4: Verification")
    print("=" * 80 + "\n")

    # Verify schema changes
    print("Schema Verification:")
    print("-" * 80)

    # Check values column exists
    values_col = conn.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'lexical_signs' AND column_name = 'values'
        """
    ).fetchone()

    if values_col:
        print("✓ lexical_signs.values column exists (TEXT[])")
    else:
        print("✗ lexical_signs.values column NOT found")

    # Check old columns removed
    old_cols = conn.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'lexical_signs'
          AND column_name IN ('logographic_values', 'syllabic_values')
        """
    ).fetchall()

    if not old_cols:
        print("✓ Old columns (logographic_values, syllabic_values) removed")
    else:
        print(f"✗ Old columns still exist: {[c[0] for c in old_cols]}")

    # Check unique constraint
    unique_constraint = conn.execute(
        """
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'lexical_signs'::regclass
          AND contype = 'u'
          AND conname LIKE '%sign_name%source%'
        """
    ).fetchone()

    if unique_constraint:
        print(f"✓ Unique constraint exists: {unique_constraint['conname']}")
    else:
        print("✗ Unique constraint NOT found")

    # Check value column in associations
    value_col = conn.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'lexical_sign_lemma_associations'
          AND column_name = 'value'
        """
    ).fetchone()

    if value_col:
        print("✓ lexical_sign_lemma_associations.value column exists")
    else:
        print("✗ lexical_sign_lemma_associations.value column NOT found")

    # Verify data counts
    print("\n" + "Data Verification:")
    print("-" * 80)

    sign_count = conn.execute(
        "SELECT COUNT(*) FROM lexical_signs WHERE source = 'epsd2-sl'"
    ).fetchone()[0]

    unique_signs = conn.execute(
        "SELECT COUNT(DISTINCT sign_name) FROM lexical_signs WHERE source = 'epsd2-sl'"
    ).fetchone()[0]

    assoc_count = conn.execute(
        "SELECT COUNT(*) FROM lexical_sign_lemma_associations WHERE source = 'epsd2-sl'"
    ).fetchone()[0]

    # Count associations with values populated
    assoc_with_values = conn.execute(
        """
        SELECT COUNT(*)
        FROM lexical_sign_lemma_associations
        WHERE source = 'epsd2-sl' AND value IS NOT NULL
        """
    ).fetchone()[0]

    lemma_count = conn.execute(
        "SELECT COUNT(*) FROM lexical_lemmas WHERE source = 'epsd2'"
    ).fetchone()[0]

    sense_count = conn.execute(
        "SELECT COUNT(*) FROM lexical_senses WHERE source = 'epsd2'"
    ).fetchone()[0]

    print(f"Signs (total):                      {sign_count:,}")
    print(f"Signs (unique names):               {unique_signs:,}")
    print(f"Sign-Lemma associations:            {assoc_count:,}")
    print(f"  └─ With values populated:         {assoc_with_values:,}")
    print(f"Lemmas:                             {lemma_count:,}")
    print(f"Senses:                             {sense_count:,}")

    # Expected results
    print("\n" + "Expected vs Actual:")
    print("-" * 80)
    print(f"Signs should be:                    2,093 (actual: {unique_signs:,})")
    print(f"Associations should be:             ~2,725 (actual: {assoc_count:,})")
    print(
        f"Associations with values:           {assoc_count:,} (actual: {assoc_with_values:,})"
    )

    # Success indicators
    print("\n" + "Status:")
    print("-" * 80)

    success = True

    if unique_signs == sign_count == 2093:
        print("✓ No duplicates - idempotency working!")
    else:
        print(
            f"⚠ Warning: Expected 2,093 unique signs, got {unique_signs:,} (total: {sign_count:,})"
        )
        success = False

    if assoc_count >= 2725:
        improvement = assoc_count - 2325
        print(
            f"✓ Association improvement: +{improvement:,} from case-insensitive matching"
        )
    elif assoc_count > 2325:
        improvement = assoc_count - 2325
        print(f"⚠ Partial improvement: +{improvement:,} (expected ~+400)")
    else:
        print(f"✗ Associations did not increase (expected ~2,725, got {assoc_count:,})")
        success = False

    if assoc_with_values == assoc_count:
        print("✓ All associations have values populated (subscripts preserved)")
    else:
        print(
            f"⚠ Warning: Only {assoc_with_values:,} / {assoc_count:,} associations have values"
        )

    return success


def main():
    settings = get_settings()

    conn = psycopg.connect(
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}",
        row_factory=psycopg.rows.dict_row,
    )

    print("\n" + "=" * 80)
    print("ePSD2 FULL FIX: ALTER SCHEMA + CLEANUP + RE-IMPORT")
    print("=" * 80)

    # Step 1: Alter schema
    if not run_alter_migration(conn):
        print("\n✗ Failed at schema alteration step")
        return 1

    # Step 2: Cleanup
    if not run_cleanup(conn):
        print("\n✗ Failed at cleanup step")
        return 1

    # Step 3: Import
    if not run_import():
        print("\n✗ Failed at import step")
        return 1

    # Step 4: Verify
    success = verify_results(conn)

    print("\n" + "=" * 80)
    if success:
        print("✓ COMPLETE - ALL CHECKS PASSED")
    else:
        print("⚠ COMPLETE - SOME WARNINGS (review output above)")
    print("=" * 80 + "\n")

    conn.close()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
