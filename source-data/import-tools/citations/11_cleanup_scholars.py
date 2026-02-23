#!/usr/bin/env python3
"""
Phase 11: Scholar deduplication and cleanup.

Populates normalized_name, classifies author_type, removes garbage entries,
and merges duplicates with full audit trail via scholar_merge_log.

Requires: migration 017_scholar_deduplication.sql

Usage:
    python 11_cleanup_scholars.py [--dry-run] [--step STEP]
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.db import get_connection
from lib.name_normalizer import parse_name, names_match

# Patterns that indicate institutional / non-person entries
INSTITUTION_PATTERNS = [
    r"^CDLI$",
    r"(?i)\buniversity\b",
    r"(?i)\bmuseum\b",
    r"(?i)\binstitut",
    r"(?i)\bacademy\b",
    r"(?i)\bsociety\b",
    r"(?i)\bfoundation\b",
    r"(?i)\bpress\b",
    r"(?i)\bproject\b",
    r"(?i)\bverlag\b",
    r"(?i)\beditions?\b",
]

PROJECT_PATTERNS = [
    r"(?i)^oracc",
    r"(?i)^etcsl",
    r"(?i)^epsd",
    r"(?i)^dcclt",
    r"(?i)^cdli$",
]

UNKNOWN_PATTERNS = [
    r"^Unknown$",
    r"^unknown$",
    r"^\s*$",
    r"^N/A$",
    r"^n/a$",
    r"^-$",
    r"^\?+$",
]

# Garbage: entries that are clearly not names
GARBAGE_PATTERNS = [
    r"^\d{4}$",  # Year numbers: "1985"
    r"^Christie",  # Auction house refs
    r"^Sotheby",
    r"(?i)^lot\s+\d+",
    r"^\d+[\s,]+\d+",  # Numeric sequences
]


def classify_author_type(name: str) -> str:
    """Determine author_type for a scholar name."""
    for pat in UNKNOWN_PATTERNS:
        if re.match(pat, name):
            return "unknown"
    for pat in PROJECT_PATTERNS:
        if re.match(pat, name):
            return "project"
    for pat in INSTITUTION_PATTERNS:
        if re.search(pat, name):
            return "institution"
    return "person"


def is_garbage(name: str) -> bool:
    """Check if name is clearly not a valid author entry."""
    for pat in GARBAGE_PATTERNS:
        if re.search(pat, name):
            return True
    # Multi-author strings: 3+ commas with no semicolons (not "Surname, Given")
    # A proper "Surname, Given" has at most 1 comma per name
    comma_count = name.count(",")
    if comma_count >= 5 and ";" not in name:
        return True
    return False


def is_multi_author_string(name: str) -> bool:
    """Detect multi-author strings stored as single scholar record."""
    # "Herbordt, Suzanne, Mattila, Raija, Parker, Barbara" pattern
    # Heuristic: 3+ commas and the pattern looks like repeating "Surname, Given"
    comma_count = name.count(",")
    if comma_count >= 3 and ";" not in name and "&" not in name:
        # Check if it looks like alternating surnames and given names
        parts = [p.strip() for p in name.split(",")]
        if len(parts) >= 4 and len(parts) % 2 == 0:
            return True
    return False


def step_a_normalize(conn, dry_run: bool) -> int:
    """Populate normalized_name for all scholars."""
    print("\n  Step A: Populating normalized_name...")
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM scholars WHERE normalized_name IS NULL")
    rows = cur.fetchall()
    print(f"    Scholars to normalize: {len(rows):,}")

    count = 0
    for scholar_id, name in rows:
        parsed = parse_name(name or "")
        norm_key = parsed.normalized_key or ""
        if not dry_run:
            cur.execute(
                "UPDATE scholars SET normalized_name = %s WHERE id = %s",
                (norm_key, scholar_id),
            )
        count += 1

    if not dry_run:
        conn.commit()
    print(f"    Normalized: {count:,}")
    return count


def step_b_classify(conn, dry_run: bool) -> dict:
    """Classify author_type for all scholars."""
    print("\n  Step B: Classifying author_type...")
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name FROM scholars WHERE author_type = 'person' OR author_type IS NULL"
    )
    rows = cur.fetchall()
    print(f"    Scholars to classify: {len(rows):,}")

    counts = {"person": 0, "institution": 0, "project": 0, "unknown": 0}
    for scholar_id, name in rows:
        atype = classify_author_type(name or "")
        counts[atype] += 1
        if atype != "person" and not dry_run:
            cur.execute(
                "UPDATE scholars SET author_type = %s WHERE id = %s",
                (atype, scholar_id),
            )

    if not dry_run:
        conn.commit()
    for k, v in counts.items():
        print(f"    {k}: {v:,}")
    return counts


def step_c_garbage(conn, dry_run: bool) -> int:
    """Remove garbage entries (with merge_log)."""
    print("\n  Step C: Removing garbage entries...")
    cur = conn.cursor()

    # Find sentinel scholar for merge_log FK (lowest-ID "Unknown")
    cur.execute("SELECT id FROM scholars WHERE name = 'Unknown' ORDER BY id LIMIT 1")
    row = cur.fetchone()
    sentinel_id = row[0] if row else None

    cur.execute("SELECT id, name FROM scholars")
    all_scholars = cur.fetchall()

    garbage_ids = []
    multi_author_ids = []

    for scholar_id, name in all_scholars:
        if not name:
            continue
        if is_garbage(name):
            garbage_ids.append((scholar_id, name))
        elif is_multi_author_string(name):
            multi_author_ids.append((scholar_id, name))

    print(f"    Garbage entries: {len(garbage_ids):,}")
    print(f"    Multi-author strings: {len(multi_author_ids):,}")

    removed = 0

    for scholar_id, name in garbage_ids:
        # Check if this scholar has publication links
        cur.execute(
            "SELECT COUNT(*) FROM publication_authors WHERE scholar_id = %s",
            (scholar_id,),
        )
        link_count = cur.fetchone()[0]

        if link_count == 0:
            if not dry_run:
                if sentinel_id:
                    cur.execute(
                        "INSERT INTO scholar_merge_log (kept_scholar_id, merged_scholar_id, merged_name, merge_reason) "
                        "VALUES (%s, %s, %s, 'garbage_cleanup')",
                        (sentinel_id, scholar_id, name),
                    )
                cur.execute("DELETE FROM scholars WHERE id = %s", (scholar_id,))
            removed += 1
        else:
            print(f"    KEPT (has {link_count} links): {name[:60]}")

    # Multi-author strings: split if they have links, delete if not
    for scholar_id, name in multi_author_ids:
        cur.execute(
            "SELECT COUNT(*) FROM publication_authors WHERE scholar_id = %s",
            (scholar_id,),
        )
        link_count = cur.fetchone()[0]

        if link_count == 0:
            if not dry_run:
                if sentinel_id:
                    cur.execute(
                        "INSERT INTO scholar_merge_log (kept_scholar_id, merged_scholar_id, merged_name, merge_reason) "
                        "VALUES (%s, %s, %s, 'garbage_cleanup')",
                        (sentinel_id, scholar_id, name),
                    )
                cur.execute("DELETE FROM scholars WHERE id = %s", (scholar_id,))
            removed += 1
        else:
            # Split into individual authors and reassign links
            if not dry_run:
                _split_multi_author(cur, scholar_id, name)
            removed += 1  # The original multi-author record gets removed

    if not dry_run:
        conn.commit()
    print(f"    Removed: {removed:,}")
    return removed


def _split_multi_author(cur, old_scholar_id: int, multi_name: str):
    """Split a multi-author string into individual scholars, reassign links."""
    # Parse comma-separated pairs: "Surname1, Given1, Surname2, Given2"
    parts = [p.strip() for p in multi_name.split(",")]
    individuals = []
    i = 0
    while i < len(parts) - 1:
        individuals.append(f"{parts[i]}, {parts[i + 1]}")
        i += 2

    if not individuals:
        return

    # Get publications linked to this multi-author record
    cur.execute(
        "SELECT publication_id, role, position FROM publication_authors WHERE scholar_id = %s",
        (old_scholar_id,),
    )
    links = cur.fetchall()

    # Create individual scholars and reassign
    for idx, ind_name in enumerate(individuals):
        parsed = parse_name(ind_name)
        # Upsert individual scholar
        cur.execute(
            "INSERT INTO scholars (name, normalized_name, author_type) VALUES (%s, %s, 'person') "
            "ON CONFLICT DO NOTHING",
            (ind_name, parsed.normalized_key),
        )
        cur.execute("SELECT id FROM scholars WHERE name = %s", (ind_name,))
        row = cur.fetchone()
        if not row:
            continue
        new_scholar_id = row[0]

        # Create links for each publication
        for pub_id, role, position in links:
            cur.execute(
                "INSERT INTO publication_authors (publication_id, scholar_id, role, position) "
                "VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (publication_id, scholar_id, role) DO NOTHING",
                (pub_id, new_scholar_id, role, position + idx),
            )

    # Log the merge and delete the multi-author record
    if individuals:
        first_scholar_name = individuals[0]
        cur.execute("SELECT id FROM scholars WHERE name = %s", (first_scholar_name,))
        row = cur.fetchone()
        kept_id = row[0] if row else 1
        cur.execute(
            "INSERT INTO scholar_merge_log (kept_scholar_id, merged_scholar_id, merged_name, merge_reason) "
            "VALUES (%s, %s, %s, 'multi_author_split')",
            (kept_id, old_scholar_id, multi_name),
        )
    cur.execute(
        "DELETE FROM publication_authors WHERE scholar_id = %s", (old_scholar_id,)
    )
    cur.execute("DELETE FROM scholars WHERE id = %s", (old_scholar_id,))


def step_d_consolidate_sentinels(conn, dry_run: bool) -> int:
    """Consolidate "Unknown" and "CDLI" to single sentinel rows each."""
    print("\n  Step D: Consolidating sentinel duplicates...")
    cur = conn.cursor()

    total_merged = 0

    for sentinel_name, sentinel_type in [
        ("Unknown", "unknown"),
        ("CDLI", "institution"),
    ]:
        cur.execute(
            "SELECT id FROM scholars WHERE name = %s ORDER BY id ASC",
            (sentinel_name,),
        )
        rows = cur.fetchall()
        if len(rows) <= 1:
            print(f"    {sentinel_name}: {len(rows)} row(s), no merge needed")
            continue

        keep_id = rows[0][0]
        dup_ids = [r[0] for r in rows[1:]]
        print(
            f"    {sentinel_name}: keeping id={keep_id}, merging {len(dup_ids):,} duplicates"
        )

        if not dry_run:
            for dup_id in dup_ids:
                # Reassign publication_authors
                cur.execute(
                    "UPDATE publication_authors SET scholar_id = %s "
                    "WHERE scholar_id = %s "
                    "AND NOT EXISTS ("
                    "  SELECT 1 FROM publication_authors pa2 "
                    "  WHERE pa2.publication_id = publication_authors.publication_id "
                    "  AND pa2.scholar_id = %s AND pa2.role = publication_authors.role"
                    ")",
                    (keep_id, dup_id, keep_id),
                )
                # Delete any remaining links that would conflict
                cur.execute(
                    "DELETE FROM publication_authors WHERE scholar_id = %s",
                    (dup_id,),
                )
                # Log
                cur.execute(
                    "INSERT INTO scholar_merge_log (kept_scholar_id, merged_scholar_id, merged_name, merge_reason) "
                    "VALUES (%s, %s, %s, 'sentinel_consolidation')",
                    (keep_id, dup_id, sentinel_name),
                )
                # Delete duplicate
                cur.execute("DELETE FROM scholars WHERE id = %s", (dup_id,))

            # Ensure correct author_type
            cur.execute(
                "UPDATE scholars SET author_type = %s WHERE id = %s",
                (sentinel_type, keep_id),
            )
            conn.commit()

        total_merged += len(dup_ids)

    print(f"    Total sentinel duplicates merged: {total_merged:,}")
    return total_merged


def step_e_exact_duplicates(conn, dry_run: bool) -> int:
    """Merge exact name duplicates (keep ORCID holder or lowest ID)."""
    print("\n  Step E: Merging exact name duplicates...")
    cur = conn.cursor()

    cur.execute(
        "SELECT name, COUNT(*) as cnt FROM scholars "
        "GROUP BY name HAVING COUNT(*) > 1 ORDER BY cnt DESC"
    )
    dup_groups = cur.fetchall()
    print(f"    Duplicate name groups: {len(dup_groups):,}")

    total_merged = 0
    for name, cnt in dup_groups:
        # Get all scholars with this exact name
        cur.execute(
            "SELECT id, orcid, author_type FROM scholars WHERE name = %s ORDER BY id ASC",
            (name,),
        )
        scholars = cur.fetchall()

        # Pick keeper: prefer one with ORCID, then lowest ID
        keep = scholars[0]
        for s in scholars:
            if s[1] and not keep[1]:  # s has ORCID, keep doesn't
                keep = s
                break

        keep_id = keep[0]
        dup_ids = [s[0] for s in scholars if s[0] != keep_id]

        if not dup_ids:
            continue

        if not dry_run:
            for dup_id in dup_ids:
                # Reassign publication_authors, skip conflicts
                cur.execute(
                    "UPDATE publication_authors SET scholar_id = %s "
                    "WHERE scholar_id = %s "
                    "AND NOT EXISTS ("
                    "  SELECT 1 FROM publication_authors pa2 "
                    "  WHERE pa2.publication_id = publication_authors.publication_id "
                    "  AND pa2.scholar_id = %s AND pa2.role = publication_authors.role"
                    ")",
                    (keep_id, dup_id, keep_id),
                )
                cur.execute(
                    "DELETE FROM publication_authors WHERE scholar_id = %s",
                    (dup_id,),
                )
                cur.execute(
                    "INSERT INTO scholar_merge_log (kept_scholar_id, merged_scholar_id, merged_name, merge_reason) "
                    "VALUES (%s, %s, %s, 'exact_duplicate')",
                    (keep_id, dup_id, name),
                )
                cur.execute("DELETE FROM scholars WHERE id = %s", (dup_id,))

            total_merged += len(dup_ids)

        if total_merged % 1000 == 0 and total_merged > 0:
            if not dry_run:
                conn.commit()
            print(f"    Merged: {total_merged:,}...", end="\r")

    if not dry_run:
        conn.commit()
    print(f"    Exact duplicates merged: {total_merged:,}")
    return total_merged


def step_f_normalized_merge(conn, dry_run: bool) -> tuple[int, list]:
    """Merge scholars with matching normalized_name (confidence >= 0.9)."""
    print("\n  Step F: Merging normalized name variants...")
    cur = conn.cursor()

    cur.execute(
        "SELECT normalized_name, COUNT(*) as cnt FROM scholars "
        "WHERE normalized_name IS NOT NULL AND normalized_name != '' "
        "AND author_type = 'person' "
        "GROUP BY normalized_name HAVING COUNT(*) > 1 "
        "ORDER BY cnt DESC"
    )
    norm_groups = cur.fetchall()
    print(f"    Normalized name groups with duplicates: {len(norm_groups):,}")

    total_merged = 0
    review_needed = []

    for norm_name, cnt in norm_groups:
        cur.execute(
            "SELECT id, name, orcid, author_type FROM scholars "
            "WHERE normalized_name = %s ORDER BY id ASC",
            (norm_name,),
        )
        scholars = cur.fetchall()

        # Skip if different author_types
        types = set(s[3] for s in scholars)
        if len(types) > 1:
            continue

        # Check for conflicting ORCIDs
        orcids = set(s[2] for s in scholars if s[2])
        if len(orcids) > 1:
            review_needed.append(
                {
                    "normalized_name": norm_name,
                    "scholars": [(s[0], s[1], s[2]) for s in scholars],
                    "reason": "conflicting_orcids",
                }
            )
            continue

        # Compute pairwise match confidence
        parsed = [(s, parse_name(s[1])) for s in scholars]

        # Pick keeper: prefer ORCID holder, then longest name, then lowest ID
        keep_idx = 0
        for i, (s, p) in enumerate(parsed):
            if s[2] and not parsed[keep_idx][0][2]:  # Has ORCID
                keep_idx = i
            elif not s[2] and not parsed[keep_idx][0][2]:
                # Prefer longer name (more complete)
                if len(s[1]) > len(parsed[keep_idx][0][1]):
                    keep_idx = i

        keep_scholar = parsed[keep_idx][0]
        keep_parsed = parsed[keep_idx][1]
        keep_id = keep_scholar[0]

        for i, (s, p) in enumerate(parsed):
            if i == keep_idx:
                continue

            confidence = names_match(keep_parsed, p)

            if confidence >= 0.9:
                if not dry_run:
                    cur.execute(
                        "UPDATE publication_authors SET scholar_id = %s "
                        "WHERE scholar_id = %s "
                        "AND NOT EXISTS ("
                        "  SELECT 1 FROM publication_authors pa2 "
                        "  WHERE pa2.publication_id = publication_authors.publication_id "
                        "  AND pa2.scholar_id = %s AND pa2.role = publication_authors.role"
                        ")",
                        (keep_id, s[0], keep_id),
                    )
                    cur.execute(
                        "DELETE FROM publication_authors WHERE scholar_id = %s",
                        (s[0],),
                    )
                    cur.execute(
                        "INSERT INTO scholar_merge_log (kept_scholar_id, merged_scholar_id, merged_name, merge_reason) "
                        "VALUES (%s, %s, %s, 'normalized_match')",
                        (keep_id, s[0], s[1]),
                    )
                    # Cascade merge_log references
                    cur.execute(
                        "UPDATE scholar_merge_log SET kept_scholar_id = %s WHERE kept_scholar_id = %s",
                        (keep_id, s[0]),
                    )
                    cur.execute("DELETE FROM scholars WHERE id = %s", (s[0],))
                total_merged += 1
            elif confidence >= 0.7:
                review_needed.append(
                    {
                        "normalized_name": norm_name,
                        "kept": (keep_id, keep_scholar[1]),
                        "candidate": (s[0], s[1]),
                        "confidence": confidence,
                        "reason": "low_confidence",
                    }
                )

    if not dry_run:
        conn.commit()

    print(f"    Normalized variants merged: {total_merged:,}")
    print(f"    Flagged for review: {len(review_needed):,}")
    return total_merged, review_needed


def main():
    parser = argparse.ArgumentParser(description="Scholar deduplication and cleanup")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without changes"
    )
    parser.add_argument("--step", type=str, help="Run only this step (a-f)")
    args = parser.parse_args()

    print("=" * 60)
    print("SCHOLAR CLEANUP & DEDUPLICATION")
    if args.dry_run:
        print("  [DRY RUN]")
    print("=" * 60)

    conn = get_connection()

    try:
        # Pre-stats
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM scholars")
        before_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT name) FROM scholars")
        before_unique = cur.fetchone()[0]
        print(f"\n  Before: {before_count:,} scholars ({before_unique:,} unique names)")

        steps = args.step.lower() if args.step else "abcdef"

        if "a" in steps:
            step_a_normalize(conn, args.dry_run)
        if "b" in steps:
            step_b_classify(conn, args.dry_run)
        if "c" in steps:
            step_c_garbage(conn, args.dry_run)
        if "d" in steps:
            step_d_consolidate_sentinels(conn, args.dry_run)
        if "e" in steps:
            step_e_exact_duplicates(conn, args.dry_run)
        if "f" in steps:
            _, review = step_f_normalized_merge(conn, args.dry_run)
            if review:
                review_path = (
                    Path(__file__).parent / "_progress" / "scholar_review.json"
                )
                review_path.parent.mkdir(parents=True, exist_ok=True)
                review_path.write_text(json.dumps(review, indent=2))
                print(f"\n  Review file: {review_path}")

        # Post-stats
        cur.execute("SELECT COUNT(*) FROM scholars")
        after_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT name) FROM scholars")
        after_unique = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM scholar_merge_log")
        merge_count = cur.fetchone()[0]

        print(f"\n  After: {after_count:,} scholars ({after_unique:,} unique names)")
        print(f"  Merge log entries: {merge_count:,}")
        print(f"  Reduction: {before_count - after_count:,} rows removed")

        cur.execute(
            "SELECT author_type, COUNT(*) FROM scholars GROUP BY author_type ORDER BY COUNT(*) DESC"
        )
        print("\n  Author type distribution:")
        for atype, cnt in cur.fetchall():
            print(f"    {atype}: {cnt:,}")

    finally:
        conn.close()

    print("\nDone.")


if __name__ == "__main__":
    main()
