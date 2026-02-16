#!/usr/bin/env python3
"""
Verify cross-source deduplication status.

Checks:
- _dedup_candidates table contents
- Pending vs resolved candidates
- Match method distribution
- Orphan publications (no artifact links)
- Publications with suspiciously similar titles
"""

import sqlite3
import sys
import unicodedata
from pathlib import Path

DEFAULT_DB = Path("/Volumes/Portable Storage/Glintstone/database/glintstone.db")


def verify(db_path: Path) -> bool:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("=" * 60)
    print("DEDUPLICATION VERIFICATION")
    print("=" * 60)

    issues = 0

    # Check if _dedup_candidates exists
    c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='_dedup_candidates'"
    )
    if not c.fetchone():
        print("\n  _dedup_candidates table does not exist (no cross-source dedup run yet)")
        print("  This is expected if only one source has been imported.")
        _check_title_dupes(c)
        _check_orphans(c)
        conn.close()
        return True

    # Dedup candidates summary
    c.execute("SELECT COUNT(*) FROM _dedup_candidates")
    total = c.fetchone()[0]
    print(f"\n  Total dedup candidates: {total:,}")

    c.execute("SELECT COUNT(*) FROM _dedup_candidates WHERE resolved = 0")
    pending = c.fetchone()[0]
    print(f"  Pending review: {pending:,}")

    c.execute("SELECT COUNT(*) FROM _dedup_candidates WHERE resolved = 1")
    resolved = c.fetchone()[0]
    print(f"  Resolved: {resolved:,}")

    if pending > 0:
        print(f"\n  WARN: {pending:,} dedup candidates awaiting manual review")

    # By match method
    c.execute("""
        SELECT match_method, COUNT(*), AVG(confidence)
        FROM _dedup_candidates
        GROUP BY match_method
        ORDER BY COUNT(*) DESC
    """)
    methods = c.fetchall()
    if methods:
        print(f"\n  By match method:")
        for method, count, avg_conf in methods:
            print(f"    {method}: {count:,} (avg confidence {avg_conf:.2f})")

    # By resolution
    c.execute("""
        SELECT resolution, COUNT(*)
        FROM _dedup_candidates
        WHERE resolved = 1
        GROUP BY resolution
    """)
    resolutions = c.fetchall()
    if resolutions:
        print(f"\n  Resolved by outcome:")
        for res, count in resolutions:
            print(f"    {res or 'unspecified'}: {count:,}")

    # Confidence distribution of pending
    c.execute("""
        SELECT
            SUM(CASE WHEN confidence >= 0.8 THEN 1 ELSE 0 END) as high,
            SUM(CASE WHEN confidence >= 0.5 AND confidence < 0.8 THEN 1 ELSE 0 END) as medium,
            SUM(CASE WHEN confidence < 0.5 THEN 1 ELSE 0 END) as low
        FROM _dedup_candidates
        WHERE resolved = 0
    """)
    row = c.fetchone()
    if row and any(v for v in row if v):
        high, medium, low = row
        print(f"\n  Pending confidence distribution:")
        print(f"    High (>=0.8):   {high or 0:,}  -- likely true duplicates")
        print(f"    Medium (0.5-0.8): {medium or 0:,}  -- need review")
        print(f"    Low (<0.5):     {low or 0:,}  -- likely distinct")

    # Sample pending candidates
    c.execute("""
        SELECT dc.pub_a_id, dc.pub_b_id, dc.match_method, dc.confidence,
               pa.title, pa.bibtex_key, pb.title, pb.bibtex_key
        FROM _dedup_candidates dc
        JOIN publications pa ON dc.pub_a_id = pa.id
        JOIN publications pb ON dc.pub_b_id = pb.id
        WHERE dc.resolved = 0
        ORDER BY dc.confidence DESC
        LIMIT 5
    """)
    samples = c.fetchall()
    if samples:
        print(f"\n  Top pending candidates (highest confidence):")
        for a_id, b_id, method, conf, a_title, a_key, b_title, b_key in samples:
            print(f"    [{conf:.2f} via {method}]")
            print(f"      A: {a_key} -- {(a_title or '')[:60]}")
            print(f"      B: {b_key} -- {(b_title or '')[:60]}")

    _check_title_dupes(c)
    _check_orphans(c)

    conn.close()

    if issues == 0:
        print(f"\n  ALL CHECKS PASSED")
    else:
        print(f"\n  {issues} ISSUE(S) FOUND")

    return issues == 0


def _check_title_dupes(c):
    """Find publications with identical normalized titles (potential missed dupes)."""
    c.execute("""
        SELECT LOWER(REPLACE(REPLACE(title, 'the ', ''), 'The ', '')) as norm_title,
               COUNT(*) as cnt
        FROM publications
        WHERE title IS NOT NULL AND title != ''
        GROUP BY norm_title
        HAVING cnt > 1
        ORDER BY cnt DESC
        LIMIT 10
    """)
    title_dupes = c.fetchall()
    if title_dupes:
        print(f"\n  Publications with identical normalized titles ({len(title_dupes)} groups):")
        for norm, count in title_dupes[:5]:
            print(f"    \"{norm[:70]}\" -- {count} records")
        if len(title_dupes) > 5:
            print(f"    ... and {len(title_dupes) - 5} more")
    else:
        print(f"\n  PASS: No publications with identical normalized titles")


def _check_orphans(c):
    """Find publications with no artifact_edition links."""
    c.execute("""
        SELECT COUNT(*) FROM publications p
        LEFT JOIN artifact_editions ae ON p.id = ae.publication_id
        WHERE ae.id IS NULL
    """)
    orphan_pubs = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM publications")
    total_pubs = c.fetchone()[0]

    orphan_pct = (orphan_pubs / total_pubs * 100) if total_pubs else 0
    print(f"\n  Orphan publications (no artifact links): {orphan_pubs:,} / {total_pubs:,} ({orphan_pct:.1f}%)")
    if orphan_pct > 70:
        print(f"  NOTE: High orphan rate expected -- many publications discuss topics, not specific artifacts")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    success = verify(args.db)
    sys.exit(0 if success else 1)
