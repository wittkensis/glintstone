#!/usr/bin/env python3
"""
Phase 6: Import KeiBi (Keilschriftbibliographie) publications.

Requires manual data acquisition first:
- Contact Tuebingen project team for bulk BibTeX export, OR
- Manual per-volume export from https://vergil.uni-tuebingen.de/keibi/

Place BibTeX files in: data/sources/KeiBi/

Provider: KeiBi - Keilschriftbibliographie

Usage:
    python 07_import_keibi.py [--reset] [--verify-only] [--bibtex-dir DIR]
"""

import argparse
import psycopg
import psycopg.errors
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.bibtex_parser import parse_bibtex_file, bibtex_to_publication
from lib.db import get_connection
from lib.publication_matcher import (
    find_match,
    ensure_dedup_table,
    record_dedup_candidate,
)
from lib.checkpoint import ImportCheckpoint

DEFAULT_BIBTEX_DIR = Path(
    "/Volumes/Portable Storage/Glintstone/source-data/sources/KeiBi"
)

PROVIDER_NAME = "KeiBi - Keilschriftbibliographie"
SOURCE_PREFIX = "keibi:"


class KeiBiImporter:
    def __init__(self, bibtex_dir: Path, reset: bool = False):
        self.bibtex_dir = bibtex_dir
        self.checkpoint = ImportCheckpoint("keibi_import", reset=reset)
        self.annotation_run_id = None

    def run(self):
        print("=" * 60)
        print("KeiBi BIBLIOGRAPHY IMPORT")
        print(f"  Provider: {PROVIDER_NAME}")
        print(f"  BibTeX dir: {self.bibtex_dir}")
        print("=" * 60)

        # Check for BibTeX files
        bib_files = sorted(self.bibtex_dir.glob("*.bib"))
        if not bib_files:
            print(f"\n  No .bib files found in {self.bibtex_dir}")
            print("  Acquisition required:")
            print("    1. Contact Tuebingen: vergil.uni-tuebingen.de/keibi/")
            print("    2. Or manual per-volume export (~80 volumes)")
            print(f"    3. Place .bib files in: {self.bibtex_dir}")
            return False

        print(f"  BibTeX files found: {len(bib_files)}")

        if self.checkpoint.is_completed():
            print("\n  Import already completed. Use --reset to reimport.")
            return True

        conn = get_connection()

        try:
            ensure_dedup_table(conn)
            self.annotation_run_id = self._ensure_annotation_run(conn)

            total_entries = 0
            for bib_file in bib_files:
                if self.checkpoint.interrupted:
                    break

                print(f"\n  Processing {bib_file.name}...")
                entries = parse_bibtex_file(bib_file)
                print(f"    Entries: {len(entries)}")

                imported = self._import_entries(conn, entries)
                total_entries += imported
                print(f"    Imported: {imported:,}")
                self.checkpoint.save()

            if not self.checkpoint.interrupted:
                self.checkpoint.save(completed=True)
                print(f"\n  Total imported: {total_entries:,}")
        finally:
            conn.close()

        self.checkpoint.print_summary()
        return not self.checkpoint.interrupted

    def _ensure_annotation_run(self, conn: psycopg.Connection) -> int:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO annotation_runs
               (source_type, source_name, method, created_at, notes)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (
                "import",
                PROVIDER_NAME,
                "import",
                datetime.now().isoformat(),
                f"KeiBi bibliography import. Provider: {PROVIDER_NAME}",
            ),
        )
        run_id = cursor.fetchone()[0]
        conn.commit()
        return run_id

    def _import_entries(self, conn: psycopg.Connection, entries: list[dict]) -> int:
        """Import parsed BibTeX entries with dedup against existing publications."""
        cursor = conn.cursor()
        count = 0

        for entry in entries:
            if self.checkpoint.interrupted:
                break

            pub = bibtex_to_publication(entry, source_prefix=SOURCE_PREFIX)
            if not pub.get("title"):
                self.checkpoint.stats["skipped"] += 1
                continue

            # Check for existing match
            match = find_match(
                {
                    "doi": pub.get("doi"),
                    "bibtex_key": entry.get("bibtex_key"),
                    "title": pub["title"],
                    "year": pub.get("year"),
                    "short_title": pub.get("short_title"),
                    "volume": pub.get("volume_in_series"),
                },
                conn,
            )

            if match.publication_id and match.confidence >= 0.8:
                # Existing match -- record as dedup candidate for review
                self.checkpoint.stats["skipped"] += 1
                continue
            elif match.publication_id and match.confidence < 0.8:
                # Uncertain match -- record for manual review
                # Insert anyway with prefixed key
                pass

            # Insert new publication
            try:
                cursor.execute(
                    """INSERT INTO publications
                       (bibtex_key, title, short_title, publication_type,
                        year, series_key, volume_in_series,
                        authors, editors, publisher, place, doi,
                        annotation_run_id, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT(bibtex_key) DO NOTHING
                       RETURNING id""",
                    (
                        pub["bibtex_key"],
                        pub["title"],
                        pub.get("short_title"),
                        pub.get("publication_type", "other"),
                        int(pub["year"]) if pub.get("year") else None,
                        pub.get("series_key"),
                        pub.get("volume_in_series"),
                        pub.get("authors_raw", "Unknown"),
                        pub.get("editors_raw"),
                        pub.get("publisher"),
                        None,  # place
                        pub.get("doi"),
                        self.annotation_run_id,
                        datetime.now().isoformat(),
                    ),
                )

                row = cursor.fetchone()
                if row is not None:
                    count += 1
                    self.checkpoint.stats["inserted"] += 1

                    # If there was an uncertain match, record for review
                    if match.publication_id and match.confidence < 0.8:
                        new_id = row[0]
                        record_dedup_candidate(
                            conn,
                            match.publication_id,
                            new_id,
                            match.method,
                            match.confidence,
                        )

            except psycopg.errors.UniqueViolation:
                conn.rollback()
                self.checkpoint.stats["skipped"] += 1

            if count % 500 == 0 and count > 0:
                conn.commit()

        conn.commit()
        return count


def verify():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM publications WHERE bibtex_key LIKE 'keibi:%'")
    keibi_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM _dedup_candidates WHERE resolved = 0")
    dedup_pending = c.fetchone()[0]
    conn.close()

    print(f"\n  KeiBi publications: {keibi_count:,}")
    print(f"  Dedup candidates pending: {dedup_pending:,}")


def main():
    parser = argparse.ArgumentParser(description="Import KeiBi bibliography")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--bibtex-dir", type=Path, default=DEFAULT_BIBTEX_DIR)
    args = parser.parse_args()

    if args.verify_only:
        verify()
        return

    importer = KeiBiImporter(args.bibtex_dir, reset=args.reset)
    success = importer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
