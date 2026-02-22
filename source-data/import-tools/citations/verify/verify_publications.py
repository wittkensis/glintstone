#!/usr/bin/env python3
"""
Verify publication import integrity.
"""

import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = Path("/Volumes/Portable Storage/Glintstone/data-model/glintstone.db")


def verify(db_path: Path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("=" * 60)
    print("PUBLICATION VERIFICATION")
    print("=" * 60)

    issues = 0

    # Counts
    c.execute("SELECT COUNT(*) FROM publications")
    total = c.fetchone()[0]
    print(f"\n  Total publications: {total:,}")

    c.execute("SELECT COUNT(*) FROM scholars")
    scholar_count = c.fetchone()[0]
    print(f"  Total scholars: {scholar_count:,}")

    c.execute("SELECT COUNT(*) FROM publication_authors")
    link_count = c.fetchone()[0]
    print(f"  Author links: {link_count:,}")

    # Duplicates check
    c.execute("""
        SELECT bibtex_key, COUNT(*) FROM publications
        GROUP BY bibtex_key HAVING COUNT(*) > 1
    """)
    dupes = c.fetchall()
    if dupes:
        print(f"\n  FAIL: {len(dupes)} duplicate bibtex_keys")
        for bk, cnt in dupes[:5]:
            print(f"    {bk}: {cnt}")
        issues += 1
    else:
        print("  PASS: No duplicate bibtex_keys")

    # DOI duplicates
    c.execute("""
        SELECT doi, COUNT(*) FROM publications
        WHERE doi IS NOT NULL
        GROUP BY doi HAVING COUNT(*) > 1
    """)
    doi_dupes = c.fetchall()
    if doi_dupes:
        print(f"  FAIL: {len(doi_dupes)} duplicate DOIs")
        issues += 1
    else:
        print("  PASS: No duplicate DOIs")

    # Type distribution
    c.execute("""
        SELECT publication_type, COUNT(*)
        FROM publications GROUP BY publication_type
        ORDER BY COUNT(*) DESC
    """)
    print("\n  Publication types:")
    for ptype, count in c.fetchall():
        print(f"    {ptype}: {count:,}")

    # Decade distribution
    c.execute("""
        SELECT (year / 10) * 10 as decade, COUNT(*)
        FROM publications WHERE year IS NOT NULL
        GROUP BY decade ORDER BY decade
    """)
    print("\n  Publications by decade:")
    for decade, count in c.fetchall():
        bar = "#" * min(count // 50, 40)
        print(f"    {int(decade)}s: {count:>5,} {bar}")

    # Series coverage
    c.execute("""
        SELECT series_key, COUNT(*)
        FROM publications WHERE series_key IS NOT NULL
        GROUP BY series_key ORDER BY COUNT(*) DESC
        LIMIT 10
    """)
    series = c.fetchall()
    if series:
        print("\n  Top series:")
        for sk, count in series:
            print(f"    {sk}: {count:,}")

    conn.close()
    return issues == 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    success = verify(args.db)
    sys.exit(0 if success else 1)
