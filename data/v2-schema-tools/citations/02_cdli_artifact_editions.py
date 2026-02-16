#!/usr/bin/env python3
"""
Phase 1B+1C: Import CDLI artifact-publication links into Glintstone v2.

Strategy: API-first with CSV fallback.
- 1B: Fetch structured publication links from CDLI API per artifact
- 1C: Parse publication_history from cdli_cat.csv for uncovered artifacts

Provider: CDLI - cdli.earth (CC0)

Usage:
    python 02_cdli_artifact_editions.py [--reset] [--csv-only] [--verify-only] [--db PATH]
"""

import argparse
import csv
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.cdli_client import CDLIClient, PROVIDER_NAME
from lib.checkpoint import ImportCheckpoint

DEFAULT_DB = Path("/Volumes/Portable Storage/Glintstone/database/glintstone.db")
CSV_PATH = Path("/Volumes/Portable Storage/Glintstone/data/sources/CDLI/metadata/cdli_cat.csv")

BATCH_SIZE = 500


class CDLIArtifactEditionImporter:
    """Imports artifact-publication links via API + CSV fallback."""

    def __init__(self, db_path: Path, reset: bool = False, csv_only: bool = False):
        self.db_path = db_path
        self.csv_only = csv_only
        self.client = CDLIClient()
        self.checkpoint = ImportCheckpoint("cdli_artifact_editions", reset=reset)
        self.annotation_run_id = None

        # Cache: bibtex_key -> publication_id
        self._pub_cache: dict[str, int] = {}
        # Track which p_numbers have API-sourced editions
        self._api_covered: set[str] = set()

    def run(self):
        print("=" * 60)
        print("CDLI ARTIFACT EDITIONS IMPORT")
        print(f"  Provider: {PROVIDER_NAME}")
        print(f"  Strategy: {'CSV only' if self.csv_only else 'API-first + CSV fallback'}")
        print("=" * 60)

        if self.checkpoint.is_completed():
            print("\n  Import already completed. Use --reset to reimport.")
            self.checkpoint.print_summary()
            return True

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")

        try:
            self.annotation_run_id = self._ensure_annotation_run(conn)
            self._load_publication_cache(conn)

            if not self.csv_only:
                # Phase 1B: API import
                print("\n  Phase 1B: API artifact-publication links...")
                self._import_from_api(conn)

            if not self.checkpoint.interrupted:
                # Phase 1C: CSV fallback for uncovered artifacts
                print("\n  Phase 1C: CSV publication_history fallback...")
                self._import_from_csv(conn)

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
                f"CDLI artifact edition links. Provider: {PROVIDER_NAME}",
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def _load_publication_cache(self, conn: sqlite3.Connection):
        """Pre-load bibtex_key -> id mapping for fast lookup."""
        cursor = conn.cursor()
        cursor.execute("SELECT id, bibtex_key FROM publications WHERE bibtex_key IS NOT NULL")
        self._pub_cache = {row[1]: row[0] for row in cursor.fetchall()}
        print(f"  Publication cache: {len(self._pub_cache):,} entries")

    # ─── Phase 1B: API Import ───────────────────────────────

    def _import_from_api(self, conn: sqlite3.Connection):
        """Fetch artifact-publication links from CDLI API."""
        cursor = conn.cursor()

        # Get all p_numbers that have artifacts in DB
        cursor.execute("SELECT p_number FROM artifacts")
        p_numbers = [row[0] for row in cursor.fetchall()]
        total = len(p_numbers)
        print(f"    Artifacts to check: {total:,}")

        batch = []
        for i, p_number in enumerate(p_numbers):
            if self.checkpoint.interrupted:
                break

            # Extract numeric id from P-number
            try:
                artifact_id = int(p_number[1:])
            except (ValueError, IndexError):
                continue

            pubs = self.client.fetch_artifact_publications(artifact_id)
            if not pubs:
                continue

            self._api_covered.add(p_number)

            for link in pubs:
                record = self._transform_api_link(p_number, link)
                if record:
                    batch.append(record)

            if len(batch) >= BATCH_SIZE:
                self._commit_editions(conn, batch)
                batch = []
                self.checkpoint.stats["processed"] = i + 1
                self.checkpoint.save()
                self.checkpoint.print_progress(i + 1, total)

        if batch and not self.checkpoint.interrupted:
            self._commit_editions(conn, batch)
            self.checkpoint.stats["processed"] = len(p_numbers)

        print(f"\n    API covered {len(self._api_covered):,} artifacts")

    def _transform_api_link(self, p_number: str, link: dict) -> dict | None:
        """Transform CDLI API publication link to artifact_editions record."""
        pub = link.get("publication", {})
        bk = pub.get("bibtexkey", "")

        pub_id = self._pub_cache.get(bk)
        if not pub_id:
            return None

        ref = link.get("exact_reference", "")
        cdli_type = link.get("publication_type", "")
        edition_type = "full_edition" if cdli_type == "primary" else "catalog_entry"

        page_start, plate_no, item_no = _parse_reference(ref)

        return {
            "p_number": p_number,
            "publication_id": pub_id,
            "reference_string": ref,
            "reference_normalized": ref.lower().strip(),
            "page_start": page_start,
            "plate_no": plate_no,
            "item_no": item_no,
            "edition_type": edition_type,
            "confidence": 1.0,
            "source": "api",
        }

    # ─── Phase 1C: CSV Fallback ─────────────────────────────

    def _import_from_csv(self, conn: sqlite3.Connection):
        """Parse publication_history from CSV for artifacts NOT covered by API."""
        if not CSV_PATH.exists():
            print(f"    CSV not found: {CSV_PATH}")
            return

        batch = []
        csv_count = 0

        with open(CSV_PATH, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)

            for row in reader:
                if self.checkpoint.interrupted:
                    break

                raw_id = row.get("id", "").strip()
                if not raw_id:
                    continue

                try:
                    p_number = f"P{int(raw_id):06d}"
                except ValueError:
                    continue

                # Skip if already covered by API
                if p_number in self._api_covered:
                    continue

                pub_history = row.get("publication_history", "").strip()
                if not pub_history:
                    continue

                # Parse semicolon-separated entries
                entries = [e.strip() for e in pub_history.split(";") if e.strip()]
                for entry_str in entries:
                    record = self._parse_publication_history_entry(p_number, entry_str)
                    if record:
                        batch.append(record)

                csv_count += 1
                if len(batch) >= BATCH_SIZE:
                    self._commit_editions(conn, batch)
                    batch = []
                    if csv_count % 10000 == 0:
                        print(f"    CSV parsed: {csv_count:,}", end="\r")

        if batch and not self.checkpoint.interrupted:
            self._commit_editions(conn, batch)

        print(f"\n    CSV parsed {csv_count:,} artifacts")

    def _parse_publication_history_entry(self, p_number: str, entry: str) -> dict | None:
        """
        Parse a single publication_history entry using tiered regex.

        Tier 1 (~60%): "ABBREV VOL (YEAR) REF" -> confidence 1.0
        Tier 2 (~25%): "Author, ABBREV VOL (YEAR) REF" -> confidence 0.7
        Tier 3 (~15%): Unparseable -> store raw, confidence 0.3
        """
        # Tier 1: Direct designation pattern
        # "ATU 3 (1993) pl. 011, W 6435,a"
        # "BagM 22 (1991) 085"
        # "UET 2 (1935) 0014"
        m = re.match(
            r"^([A-Z][A-Za-z]+(?:\s+\d+\S*)?)\s*\((\d{4})\)\s*(.*?)$",
            entry.strip(),
        )
        if m:
            designation = m.group(1).strip()
            year = m.group(2)
            reference = m.group(3).strip()

            pub_id = self._resolve_publication(designation, year)
            page_start, plate_no, item_no = _parse_reference(reference)

            return {
                "p_number": p_number,
                "publication_id": pub_id,
                "reference_string": reference or entry,
                "reference_normalized": (reference or entry).lower().strip(),
                "page_start": page_start,
                "plate_no": plate_no,
                "item_no": item_no,
                "edition_type": "full_edition",
                "confidence": 1.0 if pub_id else 0.5,
                "note": entry if not pub_id else None,
                "source": "csv_tier1",
            }

        # Tier 2: Author + designation pattern
        # "Englund, Robert K. & Nissen, Hans J., ATU 3 (1993) pl. 011"
        m2 = re.match(
            r"^(.+?),\s*([A-Z][A-Za-z]+(?:\s+\d+\S*)?)\s*\((\d{4})\)\s*(.*?)$",
            entry.strip(),
        )
        if m2:
            reference = m2.group(4).strip()
            designation = m2.group(2).strip()
            year = m2.group(3)

            pub_id = self._resolve_publication(designation, year)
            page_start, plate_no, item_no = _parse_reference(reference)

            return {
                "p_number": p_number,
                "publication_id": pub_id,
                "reference_string": reference or entry,
                "reference_normalized": (reference or entry).lower().strip(),
                "page_start": page_start,
                "plate_no": plate_no,
                "item_no": item_no,
                "edition_type": "full_edition",
                "confidence": 0.7 if pub_id else 0.4,
                "note": entry,
                "source": "csv_tier2",
            }

        # Tier 3: Unparseable -- store raw
        self.checkpoint.stats["skipped"] += 1
        return {
            "p_number": p_number,
            "publication_id": None,
            "reference_string": entry,
            "reference_normalized": entry.lower().strip(),
            "page_start": None,
            "plate_no": None,
            "item_no": None,
            "edition_type": "catalog_entry",
            "confidence": 0.3,
            "note": f"UNPARSED: {entry}",
            "source": "csv_tier3",
        }

    def _resolve_publication(self, designation: str, year: str | None) -> int | None:
        """Try to match a designation to an existing publication."""
        # Try short_title match first
        for bk, pid in self._pub_cache.items():
            # Simple heuristic: check if designation appears in bibtex_key
            if designation.replace(" ", "") in bk:
                return pid
        return None

    def _commit_editions(self, conn: sqlite3.Connection, batch: list):
        """Atomically insert artifact_editions batch."""
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN IMMEDIATE")

            for record in batch:
                pub_id = record["publication_id"]
                if not pub_id:
                    # Store as note-only record (no publication FK)
                    # Skip for now -- these go to manual curation
                    self.checkpoint.stats["skipped"] += 1
                    continue

                cursor.execute(
                    """INSERT INTO artifact_editions
                       (p_number, publication_id, reference_string,
                        reference_normalized, page_start, plate_no,
                        item_no, edition_type, confidence,
                        annotation_run_id, note)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(p_number, publication_id, reference_string) DO UPDATE SET
                           confidence = MAX(excluded.confidence, confidence),
                           note = COALESCE(note, excluded.note)""",
                    (
                        record["p_number"],
                        pub_id,
                        record["reference_string"],
                        record["reference_normalized"],
                        record["page_start"],
                        record["plate_no"],
                        record["item_no"],
                        record["edition_type"],
                        record["confidence"],
                        self.annotation_run_id,
                        record.get("note"),
                    ),
                )
                self.checkpoint.stats["inserted"] += 1

            conn.commit()
        except Exception as e:
            conn.rollback()
            self.checkpoint.record_error("batch", str(e))


def _parse_reference(ref: str) -> tuple[int | None, str | None, str | None]:
    """Parse reference string into page_start, plate_no, item_no."""
    if not ref:
        return None, None, None

    page_start = None
    plate_no = None
    item_no = None

    # Plate: "pl. 011"
    plate_match = re.search(r"[Pp]l\.?\s*(\d+)", ref)
    if plate_match:
        plate_no = plate_match.group(1)

    # Page: "p. 52" or standalone number
    page_match = re.search(r"[Pp]\.?\s*(\d+)", ref)
    if page_match and not plate_match:
        try:
            page_start = int(page_match.group(1))
        except ValueError:
            pass
    elif re.match(r"^\d+$", ref.strip()):
        try:
            page_start = int(ref.strip())
        except ValueError:
            pass

    # Item: "no. 154"
    item_match = re.search(r"[Nn]o\.?\s*(\d+\S*)", ref)
    if item_match:
        item_no = item_match.group(1)

    return page_start, plate_no, item_no


def verify(db_path: Path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM artifact_editions")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT edition_type, COUNT(*) FROM artifact_editions GROUP BY edition_type")
    by_type = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(DISTINCT p_number) FROM artifact_editions"
    )
    artifacts_with_editions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM artifacts")
    total_artifacts = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM artifact_editions WHERE confidence < 0.5"
    )
    low_confidence = cursor.fetchone()[0]

    conn.close()

    print(f"\n  Artifact editions: {total:,}")
    print(f"  Artifacts with editions: {artifacts_with_editions:,} / {total_artifacts:,}")
    print(f"  Low confidence (<0.5): {low_confidence:,}")
    print(f"\n  By edition type:")
    for etype, count in by_type:
        print(f"    {etype}: {count:,}")


def main():
    parser = argparse.ArgumentParser(description="Import CDLI artifact-publication links")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--csv-only", action="store_true", help="Skip API, only parse CSV")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    if args.verify_only:
        verify(args.db)
        return

    importer = CDLIArtifactEditionImporter(args.db, reset=args.reset, csv_only=args.csv_only)
    success = importer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
