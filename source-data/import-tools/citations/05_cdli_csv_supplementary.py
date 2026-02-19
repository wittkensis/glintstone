#!/usr/bin/env python3
"""
Phase 4: Parse supplementary citation fields from CDLI CSV.

- citation field (20,928 rows) -> scholarly_annotations type=bibliography
- published_collation (4,369 rows) -> artifact_editions type=collation
- join_information (7,367 rows) -> fragment_joins + evidence

Provider: CDLI (CC0)

Usage:
    python 05_cdli_csv_supplementary.py [--reset] [--verify-only]
"""

import argparse
import csv
import re
import psycopg
import psycopg.errors
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.db import get_connection
from lib.checkpoint import ImportCheckpoint

CSV_PATH = Path("/Volumes/Portable Storage/Glintstone/source-data/sources/CDLI/metadata/cdli_cat.csv")

PROVIDER_NAME = "CDLI"
BATCH_SIZE = 1000


class CDLISupplementaryImporter:

    def __init__(self, reset: bool = False):
        self.checkpoint = ImportCheckpoint("cdli_csv_supplementary", reset=reset)
        self.annotation_run_id = None

    def run(self):
        print("=" * 60)
        print("CDLI CSV SUPPLEMENTARY FIELDS IMPORT")
        print(f"  Provider: {PROVIDER_NAME}")
        print("=" * 60)

        if not CSV_PATH.exists():
            print(f"  CSV not found: {CSV_PATH}")
            return False

        if self.checkpoint.is_completed():
            print("\n  Import already completed. Use --reset to reimport.")
            return True

        conn = get_connection()

        try:
            self.annotation_run_id = self._ensure_annotation_run(conn)

            print("\n  Parsing citation field...")
            cite_count = self._import_citations(conn)
            print(f"    Citations imported: {cite_count:,}")

            if not self.checkpoint.interrupted:
                print("\n  Parsing published_collation field...")
                coll_count = self._import_collations(conn)
                print(f"    Collations imported: {coll_count:,}")

            if not self.checkpoint.interrupted:
                print("\n  Parsing join_information field...")
                join_count = self._import_joins(conn)
                print(f"    Join records imported: {join_count:,}")

            if not self.checkpoint.interrupted:
                self.checkpoint.save(completed=True)
                print("\n  Import completed!")
            else:
                self.checkpoint.save(completed=False)
        finally:
            conn.close()

        self.checkpoint.print_summary()
        return not self.checkpoint.interrupted

    def _ensure_annotation_run(self, conn: psycopg.Connection) -> int:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO annotation_runs
               (source_type, source_name, method, created_at, notes)
               VALUES (%s, %s, %s, %s, %s)
               RETURNING id""",
            ("import", PROVIDER_NAME, "import",
             datetime.now().isoformat(),
             "CDLI CSV supplementary fields: citation, published_collation, join_information"),
        )
        run_id = cursor.fetchone()[0]
        conn.commit()
        return run_id

    def _normalize_p_number(self, raw_id: str) -> str | None:
        if not raw_id or not raw_id.strip():
            return None
        try:
            return f"P{int(raw_id.strip()):06d}"
        except ValueError:
            return raw_id.strip() if raw_id.strip().startswith("P") else None

    def _import_citations(self, conn: psycopg.Connection) -> int:
        """Parse citation field into scholarly_annotations."""
        cursor = conn.cursor()
        count = 0

        with open(CSV_PATH, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            batch = []

            for row in reader:
                if self.checkpoint.interrupted:
                    break

                citation = row.get("citation", "").strip()
                if not citation:
                    continue

                p_number = self._normalize_p_number(row.get("id"))
                if not p_number:
                    continue

                batch.append((p_number, citation))

                if len(batch) >= BATCH_SIZE:
                    for p, cite in batch:
                        cursor.execute(
                            """INSERT INTO scholarly_annotations
                               (artifact_id, annotation_type, content,
                                annotation_run_id, confidence, visibility, created_at)
                               VALUES (%s, %s, %s, %s, %s, %s, %s)
                               ON CONFLICT DO NOTHING""",
                            (p, "bibliography", cite,
                             self.annotation_run_id, 0.8, "public",
                             datetime.now().isoformat()),
                        )
                        count += cursor.rowcount
                    conn.commit()
                    batch = []

            if batch and not self.checkpoint.interrupted:
                for p, cite in batch:
                    cursor.execute(
                        """INSERT INTO scholarly_annotations
                           (artifact_id, annotation_type, content,
                            annotation_run_id, confidence, visibility, created_at)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT DO NOTHING""",
                        (p, "bibliography", cite,
                         self.annotation_run_id, 0.8, "public",
                         datetime.now().isoformat()),
                    )
                    count += cursor.rowcount
                conn.commit()

        self.checkpoint.stats["inserted"] += count
        return count

    def _import_collations(self, conn: psycopg.Connection) -> int:
        """Parse published_collation into artifact_editions type=collation."""
        cursor = conn.cursor()
        count = 0

        # Need publication cache for matching
        cursor.execute("SELECT id, bibtex_key, short_title FROM publications")
        pub_cache = {row[1]: row[0] for row in cursor.fetchall() if row[1]}

        with open(CSV_PATH, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            batch = []

            for row in reader:
                if self.checkpoint.interrupted:
                    break

                collation = row.get("published_collation", "").strip()
                if not collation:
                    continue

                p_number = self._normalize_p_number(row.get("id"))
                if not p_number:
                    continue

                batch.append((p_number, collation))

                if len(batch) >= BATCH_SIZE:
                    count += self._flush_collation_batch(cursor, batch, pub_cache)
                    conn.commit()
                    batch = []

            if batch and not self.checkpoint.interrupted:
                count += self._flush_collation_batch(cursor, batch, pub_cache)
                conn.commit()

        self.checkpoint.stats["inserted"] += count
        return count

    def _flush_collation_batch(self, cursor, batch: list, pub_cache: dict) -> int:
        """Insert matched collations and stage unmatched ones."""
        count = 0
        for p, coll in batch:
            pub_id = self._match_collation_to_publication(coll, pub_cache)
            if pub_id:
                cursor.execute(
                    """INSERT INTO artifact_editions
                       (p_number, publication_id, reference_string,
                        reference_normalized, edition_type, confidence,
                        annotation_run_id, note)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT(p_number, publication_id, reference_string) DO NOTHING""",
                    (p, pub_id, coll, coll.lower().strip(),
                     "collation", 0.7, self.annotation_run_id, None),
                )
                count += cursor.rowcount
            else:
                self._stage_unparsed(cursor, p, coll)
        return count

    def _stage_unparsed(self, cursor, p_number: str, raw_text: str):
        """Write unmatched collation record to _unparsed_records staging table."""
        cursor.execute(
            """INSERT INTO _unparsed_records
               (source_script, p_number, raw_text, parse_tier, reason, annotation_run_id)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            ("05_cdli_csv_supplementary", p_number, raw_text,
             "collation_unmatched", "No publication match for collation string",
             self.annotation_run_id),
        )
        self.checkpoint.stats["skipped"] += 1

    def _match_collation_to_publication(self, collation_str: str, pub_cache: dict) -> int | None:
        """Try to match a collation string to a known publication."""
        # Extract designation-like patterns
        m = re.match(r"([A-Z][A-Za-z]+(?:\s+\d+)?)", collation_str)
        if m:
            designation = m.group(1).replace(" ", "")
            for bk, pid in pub_cache.items():
                if designation in bk:
                    return pid
        return None

    def _import_joins(self, conn: psycopg.Connection) -> int:
        """Parse join_information into fragment_joins."""
        cursor = conn.cursor()
        count = 0

        # Check if fragment_joins table exists
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'fragment_joins')"
        )
        if not cursor.fetchone()[0]:
            print("    fragment_joins table not found — skipping")
            return 0

        with open(CSV_PATH, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)

            for row in reader:
                if self.checkpoint.interrupted:
                    break

                join_info = row.get("join_information", "").strip()
                if not join_info:
                    continue

                p_number = self._normalize_p_number(row.get("id"))
                if not p_number:
                    continue

                # Parse join references: "P123456 + P234567" or similar
                p_numbers = re.findall(r"P\d{6}", join_info)
                for other_p in p_numbers:
                    if other_p != p_number:
                        # Ensure consistent ordering
                        a, b = sorted([p_number, other_p])
                        cursor.execute(
                            """INSERT INTO fragment_joins
                               (p_number_1, p_number_2, join_type,
                                annotation_run_id, confidence, note)
                               VALUES (%s, %s, %s, %s, %s, %s)
                               ON CONFLICT DO NOTHING""",
                            (a, b, "uncertain",
                             self.annotation_run_id, 0.6,
                             f"From CDLI join_information: {join_info}"),
                        )
                        count += cursor.rowcount

                if count % 1000 == 0 and count > 0:
                    conn.commit()

        conn.commit()
        self.checkpoint.stats["inserted"] += count
        return count


def verify():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM scholarly_annotations WHERE annotation_type = 'bibliography'")
    bib_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM artifact_editions WHERE edition_type = 'collation'")
    coll_count = c.fetchone()[0]

    c.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'fragment_joins')")
    if c.fetchone()[0]:
        c.execute("SELECT COUNT(*) FROM fragment_joins")
        join_count = c.fetchone()[0]
    else:
        join_count = "N/A (table not created)"

    conn.close()

    print(f"\n  Bibliography annotations: {bib_count:,}")
    print(f"  Collation editions: {coll_count:,}")
    print(f"  Fragment joins: {join_count}")


def main():
    parser = argparse.ArgumentParser(description="Import CDLI CSV supplementary fields")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    if args.verify_only:
        verify()
        return

    importer = CDLISupplementaryImporter(reset=args.reset)
    success = importer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
