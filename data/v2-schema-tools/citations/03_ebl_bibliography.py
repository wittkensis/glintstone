#!/usr/bin/env python3
"""
Phase 2: Import eBL (Electronic Babylonian Literature) bibliography.

Fetches fragment-level citation data from the eBL API and imports to
publications, artifact_editions, and scholarly_annotations tables.

Provider: eBL - Electronic Babylonian Literature (LMU Munich)
IMPORTANT: eBL attribution must appear in any query response that
           includes eBL-sourced data.

Usage:
    python 03_ebl_bibliography.py [--reset] [--verify-only] [--db PATH]
                                  [--token TOKEN]
"""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.ebl_client import EBLClient, PROVIDER_NAME, REFERENCE_TYPE_MAP
from lib.name_normalizer import parse_author_string
from lib.publication_matcher import find_match, ensure_dedup_table
from lib.checkpoint import ImportCheckpoint

DEFAULT_DB = Path("/Volumes/Portable Storage/Glintstone/database/glintstone.db")

BATCH_SIZE = 50


class EBLBibliographyImporter:
    """Imports eBL fragment-level bibliography with full provider attribution."""

    def __init__(self, db_path: Path, api_token: str | None = None, reset: bool = False):
        self.db_path = db_path
        self.client = EBLClient(api_token=api_token)
        self.checkpoint = ImportCheckpoint("ebl_bibliography", reset=reset)
        self.annotation_run_id = None

    def run(self):
        print("=" * 60)
        print("eBL BIBLIOGRAPHY IMPORT")
        print(f"  Provider: {PROVIDER_NAME}")
        print("  NOTE: All eBL data carries mandatory provider attribution")
        print("=" * 60)

        # Test connection
        if not self.client.test_connection():
            print("\n  Cannot connect to eBL API.")
            print("  If authentication is required, pass --token YOUR_TOKEN")
            print("  Or contact eBL team at LMU Munich for API access.")
            return False

        if self.checkpoint.is_completed():
            print("\n  Import already completed. Use --reset to reimport.")
            self.checkpoint.print_summary()
            return True

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")

        try:
            ensure_dedup_table(conn)
            self.annotation_run_id = self._ensure_annotation_run(conn)

            # Get fragments that have external_resources linking to eBL
            fragments = self._get_ebl_fragments(conn)
            print(f"  Fragments with eBL links: {len(fragments):,}")
            self.checkpoint.set_total(len(fragments))

            self._import_fragment_bibliographies(conn, fragments)

            if not self.checkpoint.interrupted:
                self.checkpoint.save(completed=True)
                print("\n  Import completed successfully!")
            else:
                self.checkpoint.save(completed=False)
                print("\n  Interrupted. Run again to resume.")
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
            (
                "import",
                PROVIDER_NAME,
                "api_fetch",
                datetime.now().isoformat(),
                f"eBL fragment bibliography import. Provider: {PROVIDER_NAME}. "
                "All records must display eBL attribution.",
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def _get_ebl_fragments(self, conn: sqlite3.Connection) -> list[tuple[str, str]]:
        """
        Get list of (p_number, ebl_fragment_id) pairs from external_resources.

        The CDLI API provides external_resource links to eBL for fragments
        that exist in both systems.
        """
        cursor = conn.cursor()

        # Check if external_resources table exists in v2
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='external_resources'"
        )
        if not cursor.fetchone():
            print("  external_resources table not found. Using artifacts with known eBL IDs.")
            return []

        cursor.execute(
            """SELECT er.p_number, er.external_key
               FROM external_resources er
               WHERE er.resource_name LIKE '%ebl%' OR er.resource_name LIKE '%eBL%'"""
        )
        return cursor.fetchall()

    def _import_fragment_bibliographies(self, conn: sqlite3.Connection, fragments: list):
        """Fetch and import bibliography for each eBL fragment."""
        batch = []

        for i, (p_number, ebl_id) in enumerate(fragments):
            if self.checkpoint.interrupted:
                break

            bib_entries = self.client.fetch_fragment_bibliography(ebl_id)
            if not bib_entries:
                self.checkpoint.stats["skipped"] += 1
                continue

            for entry in bib_entries:
                parsed = self.client.parse_bibliography_entry(entry)
                record = self._transform_entry(conn, p_number, parsed)
                if record:
                    batch.append(record)

            if len(batch) >= BATCH_SIZE:
                self._commit_batch(conn, batch)
                batch = []
                self.checkpoint.stats["processed"] = i + 1
                self.checkpoint.save()
                self.checkpoint.print_progress(i + 1, len(fragments))

        if batch and not self.checkpoint.interrupted:
            self._commit_batch(conn, batch)
            self.checkpoint.stats["processed"] = len(fragments)

    def _transform_entry(self, conn: sqlite3.Connection, p_number: str, parsed: dict) -> dict | None:
        """Transform parsed eBL bibliography entry to import record."""
        if not parsed.get("title"):
            return None

        # Try to match against existing publications
        match = find_match(
            {
                "doi": parsed.get("doi"),
                "title": parsed["title"],
                "year": parsed.get("year"),
            },
            conn,
        )

        return {
            "p_number": p_number,
            "publication_match": match,
            "title": parsed["title"],
            "authors_raw": parsed.get("authors_raw", ""),
            "year": parsed.get("year"),
            "doi": parsed.get("doi"),
            "publication_type": parsed.get("publication_type", "other"),
            "edition_type": parsed.get("edition_type", "catalog_entry"),
            "pages": parsed.get("pages", ""),
            "notes": parsed.get("notes", ""),
            "container_title": parsed.get("container_title", ""),
            "volume": parsed.get("volume"),
            "publisher": parsed.get("publisher"),
            "provider": PROVIDER_NAME,
        }

    def _commit_batch(self, conn: sqlite3.Connection, batch: list):
        """Insert publications and artifact_editions from eBL data."""
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN IMMEDIATE")

            for record in batch:
                match = record["publication_match"]

                if match.publication_id:
                    pub_id = match.publication_id
                else:
                    # Insert new publication from eBL data
                    # Generate a bibtex_key from eBL data
                    bk = self._generate_bibtex_key(record)
                    cursor.execute(
                        """INSERT INTO publications
                           (bibtex_key, title, short_title, publication_type,
                            year, authors, publisher, annotation_run_id, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                           ON CONFLICT(bibtex_key) DO NOTHING""",
                        (
                            bk,
                            record["title"],
                            None,
                            record["publication_type"],
                            int(record["year"]) if record.get("year") else None,
                            record["authors_raw"] or "Unknown",
                            record.get("publisher"),
                            self.annotation_run_id,
                            datetime.now().isoformat(),
                        ),
                    )

                    cursor.execute(
                        "SELECT id FROM publications WHERE bibtex_key = ?", (bk,)
                    )
                    row = cursor.fetchone()
                    pub_id = row[0] if row else None

                if not pub_id:
                    self.checkpoint.stats["skipped"] += 1
                    continue

                # Insert artifact_edition
                ref_str = record.get("pages") or record["title"]
                cursor.execute(
                    """INSERT INTO artifact_editions
                       (p_number, publication_id, reference_string,
                        reference_normalized, edition_type, confidence,
                        annotation_run_id, note)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(p_number, publication_id, reference_string) DO NOTHING""",
                    (
                        record["p_number"],
                        pub_id,
                        ref_str,
                        ref_str.lower().strip(),
                        record["edition_type"],
                        0.9,  # High confidence for structured eBL data
                        self.annotation_run_id,
                        f"Source: {PROVIDER_NAME}. {record.get('notes', '')}".strip(),
                    ),
                )
                self.checkpoint.stats["inserted"] += 1

            conn.commit()
        except Exception as e:
            conn.rollback()
            self.checkpoint.record_error("batch", str(e))

    @staticmethod
    def _generate_bibtex_key(record: dict) -> str:
        """Generate a bibtex_key for an eBL-sourced publication."""
        # Use DOI if available
        if record.get("doi"):
            return f"ebl:doi:{record['doi']}"

        # Otherwise: author+year+first-word
        authors = record.get("authors_raw", "Unknown")
        first_author = authors.split(";")[0].split(",")[0].strip()
        year = record.get("year", "nd")
        title_word = (record.get("title", "") or "untitled").split()[0][:10]

        return f"ebl:{first_author}{year}{title_word}"


def verify(db_path: Path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM annotation_runs WHERE source_name = ?",
        (PROVIDER_NAME,),
    )
    run_count = cursor.fetchone()[0]

    cursor.execute(
        """SELECT COUNT(*) FROM artifact_editions ae
           JOIN annotation_runs ar ON ae.annotation_run_id = ar.id
           WHERE ar.source_name = ?""",
        (PROVIDER_NAME,),
    )
    edition_count = cursor.fetchone()[0]

    cursor.execute(
        """SELECT COUNT(*) FROM publications p
           JOIN annotation_runs ar ON p.annotation_run_id = ar.id
           WHERE ar.source_name = ?""",
        (PROVIDER_NAME,),
    )
    pub_count = cursor.fetchone()[0]

    conn.close()

    print(f"\n  eBL import runs:     {run_count}")
    print(f"  eBL publications:    {pub_count:,}")
    print(f"  eBL artifact editions: {edition_count:,}")
    print(f"\n  Provider: {PROVIDER_NAME}")


def main():
    parser = argparse.ArgumentParser(description="Import eBL bibliography")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--token", type=str, default=None, help="eBL API token")
    args = parser.parse_args()

    if args.verify_only:
        verify(args.db)
        return

    importer = EBLBibliographyImporter(args.db, api_token=args.token, reset=args.reset)
    success = importer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
