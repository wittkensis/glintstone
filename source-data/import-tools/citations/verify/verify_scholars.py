#!/usr/bin/env python3
"""
Verify scholar import integrity.

Checks:
- Total scholar count
- ORCID coverage (target: >200 after OpenAlex enrichment)
- Likely duplicates (normalized name collisions)
- publication_authors coverage (what % of publications have structured authorship)
- Scholars with no publication links (orphans)
"""

import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

DEFAULT_DB = Path("/Volumes/Portable Storage/Glintstone/data-model/glintstone.db")


def _normalize_key(name: str) -> str:
    """Quick surname+initials normalization for dupe detection."""
    # Strip diacritics
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = "".join(c for c in nfkd if not unicodedata.combining(c)).lower()

    # Extract surname (last word or first word before comma)
    if "," in ascii_name:
        surname = ascii_name.split(",")[0].strip()
    else:
        parts = ascii_name.split()
        surname = parts[-1] if parts else ""

    # Extract initials from given names
    if "," in ascii_name:
        given = ascii_name.split(",", 1)[1].strip()
    else:
        parts = ascii_name.split()
        given = " ".join(parts[:-1]) if len(parts) > 1 else ""

    initials = "".join(p[0] for p in re.split(r"[\s.]+", given) if p)
    return f"{surname}_{initials}" if initials else surname


def verify(db_path: Path) -> bool:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("=" * 60)
    print("SCHOLAR VERIFICATION")
    print("=" * 60)

    issues = 0

    # Total counts
    c.execute("SELECT COUNT(*) FROM scholars")
    total = c.fetchone()[0]
    print(f"\n  Total scholars: {total:,}")

    c.execute("SELECT COUNT(*) FROM scholars WHERE orcid IS NOT NULL")
    with_orcid = c.fetchone()[0]
    orcid_pct = (with_orcid / total * 100) if total else 0
    print(f"  With ORCID: {with_orcid:,} ({orcid_pct:.1f}%)")

    c.execute("SELECT COUNT(*) FROM scholars WHERE institution IS NOT NULL")
    with_inst = c.fetchone()[0]
    print(f"  With institution: {with_inst:,}")

    c.execute("SELECT COUNT(*) FROM scholars WHERE active_since IS NOT NULL")
    with_dates = c.fetchone()[0]
    print(f"  With active_since: {with_dates:,}")

    # ORCID uniqueness
    c.execute("""
        SELECT orcid, COUNT(*) FROM scholars
        WHERE orcid IS NOT NULL
        GROUP BY orcid HAVING COUNT(*) > 1
    """)
    orcid_dupes = c.fetchall()
    if orcid_dupes:
        print(f"\n  FAIL: {len(orcid_dupes)} duplicate ORCIDs")
        for orcid, cnt in orcid_dupes[:3]:
            print(f"    {orcid}: {cnt} scholars")
        issues += 1
    else:
        print(f"  PASS: No duplicate ORCIDs")

    # Likely duplicates by normalized name
    c.execute("SELECT id, name FROM scholars")
    all_scholars = c.fetchall()

    name_groups: dict[str, list[tuple[int, str]]] = {}
    for sid, name in all_scholars:
        key = _normalize_key(name)
        if key:
            name_groups.setdefault(key, []).append((sid, name))

    likely_dupes = {k: v for k, v in name_groups.items() if len(v) > 1}
    if likely_dupes:
        print(f"\n  WARN: {len(likely_dupes)} potential duplicate groups by normalized name")
        shown = 0
        for key, group in sorted(likely_dupes.items(), key=lambda x: -len(x[1])):
            if shown >= 10:
                break
            names = [f"'{name}' (id={sid})" for sid, name in group]
            print(f"    [{key}]: {', '.join(names)}")
            shown += 1
        if len(likely_dupes) > 10:
            print(f"    ... and {len(likely_dupes) - 10} more groups")
    else:
        print(f"  PASS: No obvious name duplicates detected")

    # publication_authors coverage
    c.execute("SELECT COUNT(*) FROM publications")
    total_pubs = c.fetchone()[0]

    c.execute("SELECT COUNT(DISTINCT publication_id) FROM publication_authors")
    pubs_with_authors = c.fetchone()[0]

    author_coverage_pct = (pubs_with_authors / total_pubs * 100) if total_pubs else 0
    print(f"\n  Publications with structured authors: {pubs_with_authors:,} / {total_pubs:,} ({author_coverage_pct:.1f}%)")

    c.execute("SELECT COUNT(*) FROM publication_authors")
    total_links = c.fetchone()[0]
    print(f"  Total author links: {total_links:,}")

    # Role distribution
    c.execute("""
        SELECT role, COUNT(*)
        FROM publication_authors
        GROUP BY role
        ORDER BY COUNT(*) DESC
    """)
    print(f"\n  Author links by role:")
    for role, count in c.fetchall():
        print(f"    {role}: {count:,}")

    # Orphan scholars (no publication links)
    c.execute("""
        SELECT COUNT(*) FROM scholars s
        LEFT JOIN publication_authors pa ON s.id = pa.scholar_id
        WHERE pa.id IS NULL
    """)
    orphans = c.fetchone()[0]
    orphan_pct = (orphans / total * 100) if total else 0
    print(f"\n  Scholars with no publication links: {orphans:,} ({orphan_pct:.1f}%)")
    if orphan_pct > 50:
        print(f"  WARN: Over half of scholars have no publication links")

    # Top contributors
    c.execute("""
        SELECT s.name, COUNT(pa.id) as pub_count
        FROM scholars s
        JOIN publication_authors pa ON s.id = pa.scholar_id
        GROUP BY s.id
        ORDER BY pub_count DESC
        LIMIT 10
    """)
    top = c.fetchall()
    if top:
        print(f"\n  Top 10 scholars by publication count:")
        for name, count in top:
            print(f"    {name}: {count:,}")

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
