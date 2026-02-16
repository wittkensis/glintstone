#!/usr/bin/env python3
"""
Phase 4: Parse supplementary citation fields from CDLI CSV.

- citation field (20,928 rows) -> scholarly_annotations type=bibliography
- published_collation (4,369 rows) -> artifact_editions type=collation
- join_information (7,367 rows) -> fragment_joins + evidence

Provider: CDLI (CC0)

Usage:
    python 05_cdli_csv_supplementary.py [--reset] [--verify-only] [--db PATH]
"""

import argparse
import csv
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.checkpoint import ImportCheckpoint

DEFAULT_DB = Path("/Volumes/Portable Storage/Glintstone/database/glintstone.db")
CSV_PATH = Path("/Volumes/Portable Storage/Glintstone/data/sources/CDLI/metadata/cdli_cat.csv")

PROVIDER_NAME = "CDLI"
BATCH_SIZE = 1000


class CDLISupplementaryImporter:

    def __init__(self, db_path: Path, reset: bool = False):
        self.db_path = db_path
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

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")

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

    def _ensure_annotation_run(self, conn: sqlite3.Connection) -> int:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO annotation_runs
               (source_type, source_name, method, created_at, notes)
               VALUES (?, ?, ?, ?, ?)""",
            ("import", PROVIDER_NAME, "import",
             datetime.now().isoformat(),
             "CDLI CSV supplementary fields: citation, published_collation, join_information"),
        )
        conn.commit()
        return cursor.lastrowid

    def _normalize_p_number(self, raw_id: str) -> str | None:
        if not raw_id or not raw_id.strip():
            return None
        try:
            return f"P{int(raw_id.strip()):06d}"
        except ValueError:
            return raw_id.strip() if raw_id.strip().startswith("P") else None

    def _import_citations(self, conn: sqlite3.Connection) -> int:
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
                    cursor.execute("BEGIN IMMEDIATE")
                    for p, cite in batch:
                        cursor.execute(
                            """INSERT INTO scholarly_annotations
                               (artifact_id, annotation_type, content,
                                annotation_run_id, confidence, visibility, created_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?)
                               ON CONFLICT DO NOTHING""",
                            (p, "bibliography", cite,
                             self.annotation_run_id, 0.8, "public",
                             datetime.now().isoformat()),
                        )
                        count += cursor.rowcount
                    conn.commit()
                    batch = []

            if batch and not self.checkpoint.interrupted:
                cursor.execute("BEGIN IMMEDIATE")
                for p, cite in batch:
                    cursor.execute(
                        """INSERT INTO scholarly_annotations
                           (artifact_id, annotation_type, content,
                            annotation_run_id, confidence, visibility, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)
                           ON CONFLICT DO NOTHING""",
                        (p, "bibliography", cite,
                         self.annotation_run_id, 0.8, "public",
                         datetime.now().isoformat()),
                    )
                    count += cursor.rowcount
                conn.commit()

        self.checkpoint.stats["inserted"] += count
        return count

    def _import_collations(self, conn: sqlite3.Connection) -> int:
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
                    cursor.execute("BEGIN IMMEDIATE")
                    for p, coll in batch:
                        # Try to match to a publication
                        pub_id = self._match_collation_to_publication(coll, pub_cache)
                        if pub_id:
                            cursor.execute(
                                """INSERT INTO artifact_editions
                                   (p_number, publication_id, reference_string,
                                    reference_normalized, edition_type, confidence,
                                    annotation_run_id, note)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                   ON CONFLICT(p_number, publication_id, reference_string) DO NOTHING""",
                                (p, pub_id, coll, coll.lower().strip(),
                                 "collation", 0.7, self.annotation_run_id, None),
                            )
                            count += cursor.rowcount
                    conn.commit()
                    batch = []

            if batch and not self.checkpoint.interrupted:
                cursor.execute("BEGIN IMMEDIATE")
                for p, coll in batch:
                    pub_id = self._match_collation_to_publication(coll, pub_cache)
                    if pub_id:
                        cursor.execute(
                            """INSERT INTO artifact_editions
                               (p_number, publication_id, reference_string,
                                reference_normalized, edition_type, confidence,
                                annotation_run_id, note)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                               ON CONFLICT(p_number, publication_id, reference_string) DO NOTHING""",
                            (p, pub_id, coll, coll.lower().strip(),
                             "collation", 0.7, self.annotation_run_id, None),
                        )
                        count += cursor.rowcount
                conn.commit()

        self.checkpoint.stats["inserted"] += count
        return count

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

    def _import_joins(self, conn: sqlite3.Connection) -> int:
        """Parse join_information into fragment_joins."""
        cursor = conn.cursor()
        count = 0

        # Check if fragment_joins table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='fragment_joins'"
        )
        if not cursor.fetchone():
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
                        try:
                            cursor.execute(
                                """INSERT INTO fragment_joins
                                   (fragment_a, fragment_b, join_type,
                                    annotation_run_id, confidence, note)
                                   VALUES (?, ?, ?, ?, ?, ?)
                                   ON CONFLICT DO NOTHING""",
                                (a, b, "uncertain",
                                 self.annotation_run_id, 0.6,
                                 f"From CDLI join_information: {join_info}"),
                            )
                            count += cursor.rowcount
                        except sqlite3.IntegrityError:
                            pass

                if count % 1000 == 0 and count > 0:
                    conn.commit()

        conn.commit()
        self.checkpoint.stats["inserted"] += count
        return count


def verify(db_path: Path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM scholarly_annotations WHERE annotation_type = 'bibliography'")
    bib_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM artifact_editions WHERE edition_type = 'collation'")
    coll_count = c.fetchone()[0]

    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fragment_joins'")
    if c.fetchone():
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
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    if args.verify_only:
        verify(args.db)
        return

    importer = CDLISupplementaryImporter(args.db, reset=args.reset)
    success = importer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
