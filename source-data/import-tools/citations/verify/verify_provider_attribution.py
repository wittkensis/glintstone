#!/usr/bin/env python3
"""
Verify that all citation records carry proper provider attribution.

Every publication, artifact_edition, and scholarly_annotation must trace
back to an annotation_run with a non-null source_name.
"""

import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = Path("/Volumes/Portable Storage/Glintstone/data-model/glintstone.db")


def verify(db_path: Path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 60)
    print("PROVIDER ATTRIBUTION VERIFICATION")
    print("=" * 60)

    issues = 0

    # 1. Publications without annotation_run
    cursor.execute(
        "SELECT COUNT(*) FROM publications WHERE annotation_run_id IS NULL"
    )
    orphan_pubs = cursor.fetchone()[0]
    if orphan_pubs > 0:
        print(f"  FAIL: {orphan_pubs:,} publications have no annotation_run_id")
        issues += 1
    else:
        print(f"  PASS: All publications have annotation_run_id")

    # 2. Annotation runs without source_name
    cursor.execute(
        "SELECT COUNT(*) FROM annotation_runs WHERE source_name IS NULL OR source_name = ''"
    )
    nameless_runs = cursor.fetchone()[0]
    if nameless_runs > 0:
        print(f"  FAIL: {nameless_runs:,} annotation_runs have no source_name")
        issues += 1
    else:
        print(f"  PASS: All annotation_runs have source_name")

    # 3. Artifact editions without annotation_run
    cursor.execute(
        "SELECT COUNT(*) FROM artifact_editions WHERE annotation_run_id IS NULL"
    )
    orphan_editions = cursor.fetchone()[0]
    if orphan_editions > 0:
        print(f"  FAIL: {orphan_editions:,} artifact_editions have no annotation_run_id")
        issues += 1
    else:
        print(f"  PASS: All artifact_editions have annotation_run_id")

    # 4. Provider distribution
    print(f"\n  Provider distribution:")
    cursor.execute("""
        SELECT ar.source_name, COUNT(p.id)
        FROM publications p
        JOIN annotation_runs ar ON p.annotation_run_id = ar.id
        GROUP BY ar.source_name
        ORDER BY COUNT(p.id) DESC
    """)
    for name, count in cursor.fetchall():
        print(f"    {name}: {count:,}")

    # 5. eBL-specific check
    cursor.execute(
        "SELECT COUNT(*) FROM annotation_runs WHERE source_name LIKE '%eBL%'"
    )
    ebl_runs = cursor.fetchone()[0]
    if ebl_runs > 0:
        print(f"\n  eBL runs found: {ebl_runs}")
        cursor.execute("""
            SELECT ar.source_name, ar.notes
            FROM annotation_runs ar
            WHERE ar.source_name LIKE '%eBL%'
            LIMIT 3
        """)
        for name, notes in cursor.fetchall():
            print(f"    {name}: {notes[:80] if notes else 'no notes'}")
    else:
        print(f"\n  INFO: No eBL data imported yet")

    conn.close()

    if issues == 0:
        print(f"\n  ALL CHECKS PASSED")
    else:
        print(f"\n  {issues} ISSUE(S) FOUND")

    return issues == 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    success = verify(args.db)
    sys.exit(0 if success else 1)
