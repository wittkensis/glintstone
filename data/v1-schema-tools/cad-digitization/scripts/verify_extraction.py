#!/usr/bin/env python3
"""
Verify CAD extraction quality.

Usage:
    python verify_extraction.py
    python verify_extraction.py --verbose
    python verify_extraction.py --sample 20

This script:
1. Counts entries per volume
2. Checks for common extraction issues
3. Samples random entries for spot-checking
4. Validates cross-reference resolution
5. Reports overall statistics
"""

import argparse
import json
import random
import sqlite3
import sys
from pathlib import Path
from typing import List, Tuple


def get_db_connection(db_path: Path) -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def count_by_volume(conn: sqlite3.Connection) -> List[Tuple[str, int]]:
    """Count entries per volume."""
    cursor = conn.execute("""
        SELECT volume, COUNT(*) as count
        FROM cad_entries
        GROUP BY volume
        ORDER BY volume
    """)
    return [(row['volume'], row['count']) for row in cursor]


def check_data_quality(conn: sqlite3.Connection) -> dict:
    """Check for common data quality issues."""
    issues = {
        "empty_headwords": 0,
        "no_meanings": 0,
        "no_attestations": 0,
        "unresolved_xrefs": 0,
        "duplicate_headwords": 0,
    }

    # Empty headwords
    cursor = conn.execute("""
        SELECT COUNT(*) FROM cad_entries
        WHERE headword IS NULL OR headword = ''
    """)
    issues["empty_headwords"] = cursor.fetchone()[0]

    # Entries with no meanings
    cursor = conn.execute("""
        SELECT COUNT(*) FROM cad_entries e
        WHERE NOT EXISTS (SELECT 1 FROM cad_meanings m WHERE m.entry_id = e.id)
    """)
    issues["no_meanings"] = cursor.fetchone()[0]

    # Entries with no attestations
    cursor = conn.execute("""
        SELECT COUNT(*) FROM cad_entries e
        WHERE NOT EXISTS (SELECT 1 FROM cad_attestations a WHERE a.entry_id = e.id)
    """)
    issues["no_attestations"] = cursor.fetchone()[0]

    # Unresolved cross-references
    cursor = conn.execute("""
        SELECT COUNT(*) FROM cad_cross_references
        WHERE to_entry_id IS NULL
    """)
    issues["unresolved_xrefs"] = cursor.fetchone()[0]

    # Duplicate headwords (same headword in same volume)
    cursor = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT headword, volume, COUNT(*) as cnt
            FROM cad_entries
            GROUP BY headword, volume
            HAVING cnt > 1
        )
    """)
    issues["duplicate_headwords"] = cursor.fetchone()[0]

    return issues


def sample_entries(conn: sqlite3.Connection, n: int = 10) -> List[dict]:
    """Get random sample of entries for spot-checking."""
    cursor = conn.execute(f"""
        SELECT
            e.id,
            e.headword,
            e.part_of_speech,
            e.volume,
            (SELECT GROUP_CONCAT(m.definition, '; ')
             FROM cad_meanings m WHERE m.entry_id = e.id) as definitions,
            (SELECT COUNT(*) FROM cad_meanings m WHERE m.entry_id = e.id) as meaning_count,
            (SELECT COUNT(*) FROM cad_attestations a WHERE a.entry_id = e.id) as attestation_count
        FROM cad_entries e
        ORDER BY RANDOM()
        LIMIT {n}
    """)
    return [dict(row) for row in cursor]


def get_statistics(conn: sqlite3.Connection) -> dict:
    """Get overall statistics."""
    stats = {}

    # Entry count
    cursor = conn.execute("SELECT COUNT(*) FROM cad_entries")
    stats["total_entries"] = cursor.fetchone()[0]

    # Meaning count
    cursor = conn.execute("SELECT COUNT(*) FROM cad_meanings")
    stats["total_meanings"] = cursor.fetchone()[0]

    # Attestation count
    cursor = conn.execute("SELECT COUNT(*) FROM cad_attestations")
    stats["total_attestations"] = cursor.fetchone()[0]

    # Cross-reference count
    cursor = conn.execute("SELECT COUNT(*) FROM cad_cross_references")
    stats["total_xrefs"] = cursor.fetchone()[0]

    # Logogram count
    cursor = conn.execute("SELECT COUNT(*) FROM cad_logograms")
    stats["total_logograms"] = cursor.fetchone()[0]

    # Avg meanings per entry
    if stats["total_entries"] > 0:
        stats["avg_meanings_per_entry"] = round(
            stats["total_meanings"] / stats["total_entries"], 2
        )
        stats["avg_attestations_per_entry"] = round(
            stats["total_attestations"] / stats["total_entries"], 2
        )
    else:
        stats["avg_meanings_per_entry"] = 0
        stats["avg_attestations_per_entry"] = 0

    # Period distribution
    cursor = conn.execute("""
        SELECT period, COUNT(*) as cnt
        FROM cad_attestations
        WHERE period IS NOT NULL AND period != ''
        GROUP BY period
        ORDER BY cnt DESC
        LIMIT 10
    """)
    stats["period_distribution"] = [(row['period'], row['cnt']) for row in cursor]

    # POS distribution
    cursor = conn.execute("""
        SELECT part_of_speech, COUNT(*) as cnt
        FROM cad_entries
        WHERE part_of_speech IS NOT NULL
        GROUP BY part_of_speech
        ORDER BY cnt DESC
    """)
    stats["pos_distribution"] = [(row['part_of_speech'], row['cnt']) for row in cursor]

    return stats


def test_fts_search(conn: sqlite3.Connection, query: str = "king") -> List[dict]:
    """Test full-text search."""
    try:
        cursor = conn.execute("""
            SELECT e.headword, e.part_of_speech, m.definition
            FROM cad_fts f
            JOIN cad_entries e ON f.rowid = e.id
            LEFT JOIN cad_meanings m ON m.entry_id = e.id
            WHERE cad_fts MATCH ?
            LIMIT 5
        """, (query,))
        return [dict(row) for row in cursor]
    except sqlite3.OperationalError:
        return []


def main():
    parser = argparse.ArgumentParser(description="Verify CAD extraction quality")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--sample", "-s", type=int, default=10, help="Number of sample entries")
    parser.add_argument("--db", help="Database path")
    args = parser.parse_args()

    # Find database
    script_dir = Path(__file__).parent.parent
    if args.db:
        db_path = Path(args.db)
    else:
        candidates = [
            script_dir.parent.parent / "database" / "glintstone.db",
            Path("database/glintstone.db"),
        ]
        db_path = None
        for candidate in candidates:
            if candidate.exists():
                db_path = candidate
                break
        if not db_path:
            print("ERROR: Could not find glintstone.db")
            return 1

    print("=" * 60)
    print("CAD EXTRACTION VERIFICATION")
    print("=" * 60)
    print(f"Database: {db_path}")
    print()

    conn = get_db_connection(db_path)

    # 1. Overall statistics
    print("[1] Overall Statistics")
    print("-" * 40)
    stats = get_statistics(conn)

    print(f"  Total entries:      {stats['total_entries']:,}")
    print(f"  Total meanings:     {stats['total_meanings']:,}")
    print(f"  Total attestations: {stats['total_attestations']:,}")
    print(f"  Total cross-refs:   {stats['total_xrefs']:,}")
    print(f"  Total logograms:    {stats['total_logograms']:,}")
    print()
    print(f"  Avg meanings/entry:     {stats['avg_meanings_per_entry']}")
    print(f"  Avg attestations/entry: {stats['avg_attestations_per_entry']}")
    print()

    # 2. Per-volume counts
    print("[2] Entries by Volume")
    print("-" * 40)
    volume_counts = count_by_volume(conn)
    for volume, count in volume_counts:
        print(f"  {volume:12} {count:6,}")
    print()

    # 3. Data quality checks
    print("[3] Data Quality Checks")
    print("-" * 40)
    issues = check_data_quality(conn)

    all_good = True
    for issue_name, count in issues.items():
        status = "OK" if count == 0 else f"WARNING: {count}"
        if count > 0:
            all_good = False
        print(f"  {issue_name.replace('_', ' ').title():25} {status}")

    if all_good:
        print("  All checks passed!")
    print()

    # 4. Part of speech distribution
    if args.verbose:
        print("[4] Part of Speech Distribution")
        print("-" * 40)
        for pos, count in stats["pos_distribution"]:
            print(f"  {pos:10} {count:6,}")
        print()

        # 5. Period distribution
        print("[5] Attestation Period Distribution")
        print("-" * 40)
        for period, count in stats["period_distribution"]:
            print(f"  {period:10} {count:6,}")
        print()

    # 6. Sample entries
    print(f"[{'4' if not args.verbose else '6'}] Sample Entries (random {args.sample})")
    print("-" * 40)
    samples = sample_entries(conn, args.sample)

    for entry in samples:
        print(f"  {entry['headword']}")
        print(f"    POS: {entry['part_of_speech'] or 'N/A'}")
        print(f"    Volume: {entry['volume']}")
        print(f"    Meanings: {entry['meaning_count']}, Attestations: {entry['attestation_count']}")
        if entry['definitions']:
            # Truncate long definitions
            defs = entry['definitions'][:100]
            if len(entry['definitions']) > 100:
                defs += "..."
            print(f"    Definition: {defs}")
        print()

    # 7. FTS test
    print(f"[{'5' if not args.verbose else '7'}] Full-Text Search Test")
    print("-" * 40)
    fts_results = test_fts_search(conn, "king")
    if fts_results:
        print(f"  Search for 'king' returned {len(fts_results)} results:")
        for result in fts_results[:3]:
            print(f"    - {result['headword']}: {(result['definition'] or '')[:50]}...")
    else:
        print("  FTS index not available or empty")
    print()

    # Summary
    print("=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)

    if stats['total_entries'] == 0:
        print("WARNING: No entries found. Run import first.")
        return 1

    # Calculate quality score
    quality_score = 100
    if issues['empty_headwords'] > 0:
        quality_score -= 20
    if issues['no_meanings'] > stats['total_entries'] * 0.1:  # >10% without meanings
        quality_score -= 15
    if issues['no_attestations'] > stats['total_entries'] * 0.2:  # >20% without attestations
        quality_score -= 10
    if issues['unresolved_xrefs'] > stats['total_xrefs'] * 0.5:  # >50% unresolved
        quality_score -= 10

    print(f"Quality Score: {quality_score}/100")

    if quality_score >= 90:
        print("Status: EXCELLENT - Ready for use")
    elif quality_score >= 70:
        print("Status: GOOD - Minor issues, usable")
    elif quality_score >= 50:
        print("Status: FAIR - Some issues, review recommended")
    else:
        print("Status: POOR - Significant issues, review required")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
