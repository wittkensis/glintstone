#!/usr/bin/env python3
"""
Phase 9: Seed publication supersession chains.

Contains manually curated publication-level supersessions (well-known in the
field) plus algorithmic per-artifact supersession (newest full_edition wins).

Usage:
    python 10_seed_supersessions.py [--verify-only]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.db import get_connection

# Manually curated publication-level supersessions
# Format: (current_short_title, supersedes_short_title, scope)
KNOWN_SUPERSESSIONS = [
    # Royal Inscriptions
    ("RIME 1", None, "ED I-III royal inscriptions"),
    ("RIME 2", None, "Sargonic royal inscriptions"),
    ("RIME 3/1", None, "Gudea royal inscriptions"),
    ("RIME 3/2", None, "Ur III royal inscriptions"),
    ("RIME 4", "VAB 6", "Old Babylonian royal inscriptions"),
    ("RINAP 1", None, "Tiglath-pileser III and Shalmaneser V"),
    ("RINAP 2", None, "Sargon II"),
    ("RINAP 3/1", None, "Sennacherib part 1"),
    ("RINAP 3/2", None, "Sennacherib part 2"),
    ("RINAP 4", None, "Esarhaddon"),
    ("RINAP 5/1", None, "Ashurbanipal part 1"),
    # State Archives of Assyria
    (
        "SAA 01",
        "ABL",
        "Neo-Assyrian letters to Tiglath-pileser III and Sargon II (partial)",
    ),
    ("SAA 05", "ABL", "Neo-Assyrian letters from scholars (partial)"),
    ("SAA 10", "ABL", "Neo-Assyrian letters from scholars (partial)"),
    # Lexical texts
    (
        "DCCLT",
        "MSL",
        "Cuneiform lexical texts (digital supersedes print for covered texts)",
    ),
    # Sumerian literature
    ("ETCSL", None, "Sumerian literary texts (digital corpus)"),
    # Dictionaries
    ("ePSD2", "ePSD", "Electronic Pennsylvania Sumerian Dictionary v2 supersedes v1"),
]


def seed_supersessions():
    """Set publication-level supersedes_id chains."""
    print("=" * 60)
    print("SEED SUPERSESSION CHAINS")
    print("=" * 60)

    conn = get_connection()
    cursor = conn.cursor()

    seeded = 0
    for current_title, supersedes_title, scope in KNOWN_SUPERSESSIONS:
        if not supersedes_title:
            continue

        # Find current publication
        cursor.execute(
            "SELECT id FROM publications WHERE short_title = %s",
            (current_title,),
        )
        current = cursor.fetchone()

        # Find superseded publication
        cursor.execute(
            "SELECT id FROM publications WHERE short_title = %s",
            (supersedes_title,),
        )
        superseded = cursor.fetchone()

        if current and superseded:
            cursor.execute(
                "UPDATE publications SET supersedes_id = %s, superseded_scope = %s WHERE id = %s",
                (superseded[0], scope, current[0]),
            )
            seeded += 1
            print(f"    {current_title} supersedes {supersedes_title}")
        elif current and not superseded:
            print(f"    SKIP: {supersedes_title} not found in database")
        elif not current:
            print(f"    SKIP: {current_title} not found in database")

    conn.commit()
    print(f"\n  Publication supersessions seeded: {seeded}")

    # Algorithmic per-artifact supersession
    print("\n  Setting per-artifact is_current_edition flags...")
    cursor.execute("""
        UPDATE artifact_editions SET is_current_edition = 0
    """)

    # For each artifact, mark the newest full_edition as current
    cursor.execute("""
        UPDATE artifact_editions SET is_current_edition = 1
        WHERE id IN (
            SELECT ae.id FROM artifact_editions ae
            JOIN publications p ON ae.publication_id = p.id
            WHERE ae.edition_type = 'full_edition'
            AND ae.id = (
                SELECT ae2.id FROM artifact_editions ae2
                JOIN publications p2 ON ae2.publication_id = p2.id
                WHERE ae2.p_number = ae.p_number
                AND ae2.edition_type = 'full_edition'
                ORDER BY p2.year DESC NULLS LAST, ae2.confidence DESC
                LIMIT 1
            )
        )
    """)
    current_count = cursor.rowcount
    conn.commit()
    print(f"  Artifacts with current edition set: {current_count:,}")

    # Verify no artifact has multiple current editions
    cursor.execute("""
        SELECT p_number, COUNT(*) as cnt
        FROM artifact_editions
        WHERE is_current_edition = 1
        GROUP BY p_number
        HAVING COUNT(*) > 1
    """)
    conflicts = cursor.fetchall()
    if conflicts:
        print(
            f"\n  WARNING: {len(conflicts)} artifacts have multiple current editions!"
        )
        for p, cnt in conflicts[:5]:
            print(f"    {p}: {cnt} current editions")
    else:
        print("  No conflicts: each artifact has at most 1 current edition")

    conn.close()


def verify():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM publications WHERE supersedes_id IS NOT NULL")
    sup_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM artifact_editions WHERE is_current_edition = 1")
    current_count = c.fetchone()[0]
    c.execute(
        "SELECT COUNT(DISTINCT p_number) FROM artifact_editions WHERE is_current_edition = 1"
    )
    artifacts_with_current = c.fetchone()[0]
    conn.close()

    print(f"\n  Publication supersession chains: {sup_count:,}")
    print(f"  Artifact current editions: {current_count:,}")
    print(f"  Artifacts with current edition: {artifacts_with_current:,}")


def main():
    parser = argparse.ArgumentParser(description="Seed supersession chains")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    if args.verify_only:
        verify()
        return

    seed_supersessions()


if __name__ == "__main__":
    main()
