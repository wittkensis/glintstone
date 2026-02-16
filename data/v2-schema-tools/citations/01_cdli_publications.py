#!/usr/bin/env python3
"""
Phase 1A: Import CDLI publications into Glintstone v2 database.

Dynamically fetches publication records from the CDLI API (cdli.earth),
caches locally, and imports to the publications, scholars, and
publication_authors tables.

Provider: CDLI - cdli.earth (CC0)

Usage:
    python 01_cdli_publications.py [--reset] [--verify-only] [--db PATH]
"""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.cdli_client import CDLIClient, PROVIDER_NAME
from lib.bibtex_parser import cdli_entry_type_to_publication_type, parse_series_designation
from lib.name_normalizer import parse_author_string
from lib.checkpoint import ImportCheckpoint

DEFAULT_DB = Path("/Volumes/Portable Storage/Glintstone/database/glintstone.db")

ANNOTATION_RUN_SOURCE_TYPE = "import"
ANNOTATION_RUN_SOURCE_NAME = PROVIDER_NAME
ANNOTATION_RUN_METHOD = "api_fetch"

BATCH_SIZE = 100


class CDLIPublicationImporter:
    """Imports CDLI publications via dynamic API retrieval."""

    def __init__(self, db_path: Path, reset: bool = False):
        self.db_path = db_path
        self.client = CDLIClient()
        self.checkpoint = ImportCheckpoint("cdli_publications", reset=reset)
        self.annotation_run_id = None

    def run(self):
        print("=" * 60)
        print("CDLI PUBLICATIONS IMPORT")
        print(f"  Provider: {PROVIDER_NAME}")
        print("=" * 60)

        # Estimate total
        total_pages = self.client.estimate_total_pages()
        total_est = total_pages * 100
        print(f"  Estimated publications: ~{total_est:,}")
        self.checkpoint.set_total(total_est)

        if self.checkpoint.is_completed():
            print("\n  Import already completed. Use --reset to reimport.")
            self.checkpoint.print_summary()
            return True

        resume_page = (self.checkpoint.resume_offset // 100) + 1
        if resume_page > 1:
            print(f"  Resuming from page {resume_page}")

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")

        try:
            self.annotation_run_id = self._ensure_annotation_run(conn)
            self._import_publications(conn, resume_page, total_pages)

            if not self.checkpoint.interrupted:
                self.checkpoint.save(completed=True)
                print("\n  Import completed successfully!")
            else:
                self.checkpoint.save(completed=False)
                print(f"\n  Interrupted. Run again to resume.")
        finally:
            conn.close()

        self.checkpoint.print_summary()
        return not self.checkpoint.interrupted

    def _ensure_annotation_run(self, conn: sqlite3.Connection) -> int:
        """Create or get annotation_run for this import."""
        cursor = conn.cursor()

        # Check for existing run from a previous (interrupted) import
        cursor.execute(
            "SELECT id FROM annotation_runs WHERE source_name = ? AND source_type = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (ANNOTATION_RUN_SOURCE_NAME, ANNOTATION_RUN_SOURCE_TYPE),
        )
        row = cursor.fetchone()
        if row and not self.checkpoint.state.get("completed"):
            return row[0]

        cursor.execute(
            """INSERT INTO annotation_runs
               (source_type, source_name, method, created_at, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (
                ANNOTATION_RUN_SOURCE_TYPE,
                ANNOTATION_RUN_SOURCE_NAME,
                ANNOTATION_RUN_METHOD,
                datetime.now().isoformat(),
                f"CDLI publications API import. Provider: {PROVIDER_NAME}",
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def _import_publications(self, conn: sqlite3.Connection, start_page: int, total_pages: int):
        """Iterate API pages and import publications."""
        page = start_page
        batch = []

        while page <= total_pages and not self.checkpoint.interrupted:
            result = self.client.fetch_publications_page(page)
            if not result or not result.get("data"):
                break

            for pub_raw in result["data"]:
                record = self._transform_publication(pub_raw)
                if record:
                    batch.append((record, pub_raw))

                if len(batch) >= BATCH_SIZE:
                    self._commit_batch(conn, batch)
                    batch = []
                    self.checkpoint.stats["processed"] = (page - 1) * 100 + len(result["data"])
                    self.checkpoint.save()
                    self.checkpoint.print_progress(
                        self.checkpoint.stats["processed"],
                        total_pages * 100,
                    )

            page += 1

        # Final batch
        if batch and not self.checkpoint.interrupted:
            self._commit_batch(conn, batch)
            self.checkpoint.stats["processed"] = (page - 1) * 100

    def _transform_publication(self, raw: dict) -> dict | None:
        """Transform CDLI API publication to v2 schema record."""
        bibtex_key = raw.get("bibtexkey", "")
        if not bibtex_key:
            return None

        designation = raw.get("designation", "")
        series_key, volume = parse_series_designation(designation)

        # Fallback series extraction from series field
        if not series_key and raw.get("series"):
            series_key, volume = parse_series_designation(raw["series"])

        pub_type = cdli_entry_type_to_publication_type(raw.get("entry_type_id", 8))

        # Build authors string from nested author objects if available
        authors_raw = ""
        if "authors" in raw and isinstance(raw["authors"], list):
            author_names = []
            for a in raw["authors"]:
                if isinstance(a, dict):
                    name = a.get("author", a.get("name", ""))
                    if name:
                        author_names.append(name)
                elif isinstance(a, str):
                    author_names.append(a)
            authors_raw = "; ".join(author_names)
        elif "author" in raw:
            authors_raw = raw["author"]

        editors_raw = ""
        if "editors" in raw and isinstance(raw["editors"], list):
            editor_names = []
            for e in raw["editors"]:
                if isinstance(e, dict):
                    name = e.get("editor", e.get("name", ""))
                    if name:
                        editor_names.append(name)
                elif isinstance(e, str):
                    editor_names.append(e)
            editors_raw = "; ".join(editor_names)
        elif "editor" in raw:
            editors_raw = raw["editor"]

        return {
            "bibtex_key": bibtex_key,
            "title": raw.get("title", ""),
            "short_title": designation or None,
            "publication_type": pub_type,
            "year": self._parse_year(raw.get("year")),
            "series_key": series_key,
            "volume_in_series": volume or raw.get("number"),
            "authors": authors_raw or "Unknown",
            "editors": editors_raw or None,
            "publisher": raw.get("publisher"),
            "place": raw.get("address"),
            "annotation_run_id": self.annotation_run_id,
        }

    def _commit_batch(self, conn: sqlite3.Connection, batch: list):
        """Atomically insert/update a batch of publications."""
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN IMMEDIATE")

            for record, raw in batch:
                # UPSERT publication
                cursor.execute(
                    """INSERT INTO publications
                       (bibtex_key, title, short_title, publication_type, year,
                        series_key, volume_in_series, authors, editors,
                        publisher, place, annotation_run_id, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(bibtex_key) DO UPDATE SET
                           title = COALESCE(excluded.title, title),
                           short_title = COALESCE(excluded.short_title, short_title),
                           publication_type = COALESCE(excluded.publication_type, publication_type),
                           year = COALESCE(excluded.year, year),
                           series_key = COALESCE(excluded.series_key, series_key),
                           volume_in_series = COALESCE(excluded.volume_in_series, volume_in_series),
                           publisher = COALESCE(excluded.publisher, publisher),
                           place = COALESCE(excluded.place, place)""",
                    (
                        record["bibtex_key"],
                        record["title"],
                        record["short_title"],
                        record["publication_type"],
                        record["year"],
                        record["series_key"],
                        record["volume_in_series"],
                        record["authors"],
                        record["editors"],
                        record["publisher"],
                        record["place"],
                        record["annotation_run_id"],
                        datetime.now().isoformat(),
                    ),
                )

                if cursor.rowcount > 0:
                    self.checkpoint.stats["inserted"] += 1
                else:
                    self.checkpoint.stats["updated"] += 1

                # Get publication_id for author linking
                pub_id = cursor.lastrowid or cursor.execute(
                    "SELECT id FROM publications WHERE bibtex_key = ?",
                    (record["bibtex_key"],),
                ).fetchone()[0]

                # Insert scholars and publication_authors
                self._link_authors(cursor, pub_id, record["authors"], "author")
                if record["editors"]:
                    self._link_authors(cursor, pub_id, record["editors"], "editor")

            conn.commit()
        except Exception as e:
            conn.rollback()
            self.checkpoint.record_error(
                batch[0][0].get("bibtex_key", "unknown") if batch else "unknown",
                str(e),
            )

    def _link_authors(self, cursor, pub_id: int, authors_raw: str, role: str):
        """Parse author string and create scholar + publication_author records."""
        names = parse_author_string(authors_raw)

        for i, name in enumerate(names):
            if not name.raw.strip():
                continue

            # UPSERT scholar by normalized name
            cursor.execute(
                """INSERT INTO scholars (name)
                   VALUES (?)
                   ON CONFLICT DO NOTHING""",
                (name.raw,),
            )

            # Find scholar id (could be existing)
            cursor.execute(
                "SELECT id FROM scholars WHERE name = ?",
                (name.raw,),
            )
            row = cursor.fetchone()
            if not row:
                continue
            scholar_id = row[0]

            # UPSERT publication_authors link
            cursor.execute(
                """INSERT INTO publication_authors
                   (publication_id, scholar_id, role, position)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(publication_id, scholar_id, role) DO UPDATE SET
                       position = excluded.position""",
                (pub_id, scholar_id, role, i + 1),
            )

    @staticmethod
    def _parse_year(year_val) -> int | None:
        if year_val is None:
            return None
        try:
            return int(str(year_val).strip()[:4])
        except (ValueError, TypeError):
            return None


def verify(db_path: Path):
    """Quick verification of import results."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM publications")
    pub_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM scholars")
    scholar_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM publication_authors")
    author_link_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT publication_type, COUNT(*) FROM publications GROUP BY publication_type ORDER BY COUNT(*) DESC"
    )
    type_dist = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) FROM annotation_runs WHERE source_name = ?",
        (PROVIDER_NAME,),
    )
    run_count = cursor.fetchone()[0]

    conn.close()

    print(f"\n  Publications: {pub_count:,}")
    print(f"  Scholars:     {scholar_count:,}")
    print(f"  Author links: {author_link_count:,}")
    print(f"  Import runs:  {run_count}")
    print(f"\n  Publications by type:")
    for ptype, count in type_dist:
        print(f"    {ptype}: {count:,}")


def main():
    parser = argparse.ArgumentParser(description="Import CDLI publications")
    parser.add_argument("--reset", action="store_true", help="Reset and start fresh")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing import")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Database path")
    args = parser.parse_args()

    if args.verify_only:
        verify(args.db)
        return

    importer = CDLIPublicationImporter(args.db, reset=args.reset)
    success = importer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
