#!/usr/bin/env python3
"""
Verify artifact edition import integrity.

Checks:
- Edition counts and distributions by type
- is_current_edition uniqueness (at most 1 per artifact)
- supersedes_id chain has no cycles
- All publication_id FKs resolve
- Coverage: what % of artifacts have editions
- Low-confidence edition count
"""

import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = Path("/Volumes/Portable Storage/Glintstone/data-model/glintstone.db")


def verify(db_path: Path) -> bool:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("=" * 60)
    print("ARTIFACT EDITION VERIFICATION")
    print("=" * 60)

    issues = 0

    # Total counts
    c.execute("SELECT COUNT(*) FROM artifact_editions")
    total = c.fetchone()[0]
    print(f"\n  Total artifact editions: {total:,}")

    c.execute("SELECT COUNT(DISTINCT p_number) FROM artifact_editions")
    artifacts_with = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM artifacts")
    total_artifacts = c.fetchone()[0]

    coverage_pct = (artifacts_with / total_artifacts * 100) if total_artifacts else 0
    print(
        f"  Artifacts with editions: {artifacts_with:,} / {total_artifacts:,} ({coverage_pct:.1f}%)"
    )

    # Edition type distribution
    c.execute("""
        SELECT edition_type, COUNT(*)
        FROM artifact_editions
        GROUP BY edition_type
        ORDER BY COUNT(*) DESC
    """)
    print("\n  By edition type:")
    for etype, count in c.fetchall():
        print(f"    {etype}: {count:,}")

    # is_current_edition uniqueness
    c.execute("""
        SELECT p_number, COUNT(*) as cnt
        FROM artifact_editions
        WHERE is_current_edition = 1
        GROUP BY p_number
        HAVING cnt > 1
    """)
    conflicts = c.fetchall()
    if conflicts:
        print(f"\n  FAIL: {len(conflicts)} artifacts have multiple current editions")
        for p, cnt in conflicts[:5]:
            print(f"    {p}: {cnt} current editions")
        if len(conflicts) > 5:
            print(f"    ... and {len(conflicts) - 5} more")
        issues += 1
    else:
        c.execute("SELECT COUNT(*) FROM artifact_editions WHERE is_current_edition = 1")
        current_count = c.fetchone()[0]
        print(
            f"\n  PASS: is_current_edition uniqueness OK ({current_count:,} artifacts with current edition)"
        )

    # supersedes_id cycle detection (walk chains up to depth 20)
    c.execute("""
        SELECT id, supersedes_id FROM artifact_editions
        WHERE supersedes_id IS NOT NULL
    """)
    edges = {row[0]: row[1] for row in c.fetchall()}
    cycle_found = False
    for start in edges:
        visited = set()
        node = start
        while node in edges and node not in visited:
            visited.add(node)
            node = edges[node]
            if len(visited) > 20:
                break
        if node in visited:
            print(
                f"\n  FAIL: Cycle detected in supersedes_id chain involving edition {start}"
            )
            cycle_found = True
            issues += 1
            break
    if not cycle_found:
        chain_count = len(edges)
        print(f"  PASS: No cycles in supersedes_id chains ({chain_count:,} chains)")

    # FK integrity: all publication_ids resolve
    c.execute("""
        SELECT COUNT(*) FROM artifact_editions ae
        LEFT JOIN publications p ON ae.publication_id = p.id
        WHERE p.id IS NULL
    """)
    orphan_editions = c.fetchone()[0]
    if orphan_editions > 0:
        print(
            f"\n  FAIL: {orphan_editions:,} artifact_editions reference non-existent publications"
        )
        issues += 1
    else:
        print("  PASS: All publication_id FKs resolve")

    # FK integrity: all p_numbers resolve
    c.execute("""
        SELECT COUNT(*) FROM artifact_editions ae
        LEFT JOIN artifacts a ON ae.p_number = a.p_number
        WHERE a.p_number IS NULL
    """)
    orphan_pnums = c.fetchone()[0]
    if orphan_pnums > 0:
        print(
            f"  WARN: {orphan_pnums:,} artifact_editions reference non-existent artifacts"
        )
    else:
        print("  PASS: All p_number FKs resolve")

    # Confidence distribution
    c.execute("""
        SELECT
            SUM(CASE WHEN confidence >= 0.9 THEN 1 ELSE 0 END) as high,
            SUM(CASE WHEN confidence >= 0.5 AND confidence < 0.9 THEN 1 ELSE 0 END) as medium,
            SUM(CASE WHEN confidence < 0.5 THEN 1 ELSE 0 END) as low
        FROM artifact_editions
    """)
    high, medium, low = c.fetchone()
    print("\n  Confidence distribution:")
    print(f"    High (>=0.9):   {high or 0:,}")
    print(f"    Medium (0.5-0.9): {medium or 0:,}")
    print(f"    Low (<0.5):     {low or 0:,}")

    # Editions per artifact distribution
    c.execute("""
        SELECT
            CASE
                WHEN cnt = 1 THEN '1'
                WHEN cnt BETWEEN 2 AND 5 THEN '2-5'
                WHEN cnt BETWEEN 6 AND 10 THEN '6-10'
                WHEN cnt BETWEEN 11 AND 20 THEN '11-20'
                ELSE '20+'
            END as bucket,
            COUNT(*) as artifact_count
        FROM (
            SELECT p_number, COUNT(*) as cnt
            FROM artifact_editions
            GROUP BY p_number
        )
        GROUP BY bucket
        ORDER BY MIN(cnt)
    """)
    print("\n  Editions per artifact:")
    for bucket, count in c.fetchall():
        print(f"    {bucket} editions: {count:,} artifacts")

    # Spot check: artifacts with >20 editions (potential data quality issue)
    c.execute("""
        SELECT p_number, COUNT(*) as cnt
        FROM artifact_editions
        GROUP BY p_number
        HAVING cnt > 20
        ORDER BY cnt DESC
        LIMIT 5
    """)
    heavy = c.fetchall()
    if heavy:
        print("\n  NOTE: Artifacts with >20 editions (review for data quality):")
        for p, cnt in heavy:
            print(f"    {p}: {cnt} editions")

    # Provider distribution
    c.execute("""
        SELECT ar.source_name, COUNT(ae.id)
        FROM artifact_editions ae
        JOIN annotation_runs ar ON ae.annotation_run_id = ar.id
        GROUP BY ar.source_name
        ORDER BY COUNT(ae.id) DESC
    """)
    print("\n  By provider:")
    for name, count in c.fetchall():
        print(f"    {name}: {count:,}")

    conn.close()

    if issues == 0:
        print("\n  ALL CHECKS PASSED")
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
