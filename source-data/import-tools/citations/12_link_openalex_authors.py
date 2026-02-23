#!/usr/bin/env python3
"""
Phase 12: Link OpenAlex publication authors to scholars.

Parses the authors TEXT field on OpenAlex-sourced publications,
creates/matches scholar records, and populates publication_authors.

Requires: migration 017, script 11 (scholar cleanup) run first.

Usage:
    python 12_link_openalex_authors.py [--reset] [--verify-only] [--batch-size N]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.db import get_connection
from lib.name_normalizer import parse_author_string
from lib.checkpoint import ImportCheckpoint


BATCH_SIZE = 1000


class OpenAlexAuthorLinker:
    def __init__(self, reset: bool = False, batch_size: int = BATCH_SIZE):
        self.checkpoint = ImportCheckpoint("openalex_author_linking", reset=reset)
        self.batch_size = batch_size
        # In-memory cache: normalized_name -> scholar_id
        self._scholar_cache: dict[str, int] = {}

    def run(self):
        print("=" * 60)
        print("OPENALEX AUTHOR LINKING")
        print("=" * 60)

        if self.checkpoint.is_completed():
            print("\n  Linking already completed. Use --reset to re-run.")
            return True

        conn = get_connection()

        try:
            cur = conn.cursor()

            # Load OpenAlex publications with authors but no publication_authors links
            cur.execute(
                "SELECT p.id, p.authors FROM publications p "
                "JOIN annotation_runs ar ON p.annotation_run_id = ar.id "
                "WHERE ar.source_name = 'OpenAlex' "
                "AND p.authors IS NOT NULL AND p.authors != '' AND p.authors != 'Unknown' "
                "AND NOT EXISTS ("
                "  SELECT 1 FROM publication_authors pa WHERE pa.publication_id = p.id"
                ") "
                "ORDER BY p.id"
            )
            pubs = cur.fetchall()
            total = len(pubs)
            print(f"  OpenAlex pubs needing author links: {total:,}")
            self.checkpoint.set_total(total)

            # Warm the scholar cache
            self._warm_cache(cur)

            resume_from = self.checkpoint.resume_offset
            if resume_from > 0:
                pubs = pubs[resume_from:]
                print(f"  Resuming from offset {resume_from:,}")

            for i, (pub_id, authors_str) in enumerate(pubs):
                if self.checkpoint.interrupted:
                    break

                self._link_pub_authors(cur, pub_id, authors_str)

                self.checkpoint.stats["processed"] = resume_from + i + 1

                if (i + 1) % self.batch_size == 0:
                    conn.commit()
                    self.checkpoint.save()
                    self.checkpoint.print_progress(resume_from + i + 1, total)

            conn.commit()

            if not self.checkpoint.interrupted:
                self.checkpoint.save(completed=True)
                print("\n  Linking completed!")
            else:
                self.checkpoint.save(completed=False)
        finally:
            conn.close()

        self.checkpoint.print_summary()
        return not self.checkpoint.interrupted

    def _warm_cache(self, cur):
        """Load existing scholars into memory for fast lookup."""
        cur.execute("SELECT id, name, normalized_name FROM scholars")
        rows = cur.fetchall()
        for sid, name, norm in rows:
            if norm:
                self._scholar_cache[norm] = sid
            if name:
                # Also key by exact name for fallback
                self._scholar_cache[f"exact:{name}"] = sid
        print(f"  Scholar cache: {len(rows):,} scholars loaded")

    def _link_pub_authors(self, cur, pub_id: int, authors_str: str):
        """Parse author string, upsert scholars, create publication_authors."""
        # OpenAlex uses "; " as delimiter
        names = parse_author_string(authors_str)

        for position, parsed in enumerate(names, 1):
            if not parsed.raw.strip():
                continue

            scholar_id = self._find_or_create_scholar(cur, parsed)
            if not scholar_id:
                continue

            cur.execute(
                "INSERT INTO publication_authors (publication_id, scholar_id, role, position) "
                "VALUES (%s, %s, 'author', %s) "
                "ON CONFLICT (publication_id, scholar_id, role) DO NOTHING",
                (pub_id, scholar_id, position),
            )
            self.checkpoint.stats["inserted"] = (
                self.checkpoint.stats.get("inserted", 0) + cur.rowcount
            )

    def _find_or_create_scholar(self, cur, parsed) -> int | None:
        """Find existing scholar by normalized_name or create new one."""
        norm_key = parsed.normalized_key
        if not norm_key:
            return None

        # Check cache by normalized key
        cached = self._scholar_cache.get(norm_key)
        if cached:
            return cached

        # Check cache by exact name
        exact_key = f"exact:{parsed.raw}"
        cached = self._scholar_cache.get(exact_key)
        if cached:
            return cached

        # Check DB by normalized_name
        cur.execute(
            "SELECT id FROM scholars WHERE normalized_name = %s LIMIT 1",
            (norm_key,),
        )
        row = cur.fetchone()
        if row:
            self._scholar_cache[norm_key] = row[0]
            return row[0]

        # Check DB by exact name
        cur.execute(
            "SELECT id FROM scholars WHERE name = %s LIMIT 1",
            (parsed.raw,),
        )
        row = cur.fetchone()
        if row:
            self._scholar_cache[norm_key] = row[0]
            self._scholar_cache[exact_key] = row[0]
            return row[0]

        # Create new scholar
        cur.execute(
            "INSERT INTO scholars (name, normalized_name, author_type) "
            "VALUES (%s, %s, 'person') RETURNING id",
            (parsed.raw, norm_key),
        )
        new_id = cur.fetchone()[0]
        self._scholar_cache[norm_key] = new_id
        self._scholar_cache[exact_key] = new_id
        self.checkpoint.stats["updated"] = self.checkpoint.stats.get("updated", 0) + 1
        return new_id


def verify():
    """Verify OpenAlex author linking results."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM scholars")
    total_scholars = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM publication_authors")
    total_links = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(DISTINCT p.id) FROM publications p "
        "JOIN annotation_runs ar ON p.annotation_run_id = ar.id "
        "WHERE ar.source_name = 'OpenAlex'"
    )
    oa_pubs = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(DISTINCT pa.publication_id) FROM publication_authors pa "
        "JOIN publications p ON pa.publication_id = p.id "
        "JOIN annotation_runs ar ON p.annotation_run_id = ar.id "
        "WHERE ar.source_name = 'OpenAlex'"
    )
    oa_linked = cur.fetchone()[0]

    cur.execute(
        "SELECT author_type, COUNT(*) FROM scholars GROUP BY author_type ORDER BY COUNT(*) DESC"
    )
    type_dist = cur.fetchall()

    # Sample: show a multi-author pub
    cur.execute(
        "SELECT p.id, p.title, p.authors FROM publications p "
        "JOIN annotation_runs ar ON p.annotation_run_id = ar.id "
        "WHERE ar.source_name = 'OpenAlex' AND p.authors LIKE '%%;%%' "
        "LIMIT 1"
    )
    sample = cur.fetchone()

    conn.close()

    print(f"\n  Total scholars: {total_scholars:,}")
    print(f"  Total author links: {total_links:,}")
    print(f"  OpenAlex publications: {oa_pubs:,}")
    print(f"  OpenAlex pubs with author links: {oa_linked:,}")
    print(f"  Unlinked: {oa_pubs - oa_linked:,}")
    print("\n  Author type distribution:")
    for atype, cnt in type_dist:
        print(f"    {atype}: {cnt:,}")

    if sample:
        print(f"\n  Sample multi-author pub (id={sample[0]}):")
        print(f"    Title: {sample[1][:80]}")
        print(f"    Authors field: {sample[2][:80]}")


def main():
    parser = argparse.ArgumentParser(description="Link OpenAlex authors to scholars")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()

    if args.verify_only:
        verify()
        return

    linker = OpenAlexAuthorLinker(reset=args.reset, batch_size=args.batch_size)
    success = linker.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
