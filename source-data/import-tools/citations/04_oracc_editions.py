#!/usr/bin/env python3
"""
Phase 3: Import ORACC project editions and scholar credits.

Registers each ORACC project as a digital_edition publication,
extracts scholar names from credits fields, and creates
artifact_editions for every P-number in ORACC catalogues.

Provider: ORACC/{project_name}

Usage:
    python 04_oracc_editions.py [--reset] [--verify-only]
"""

import argparse
import json
import re
import psycopg
import psycopg.errors
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.db import get_connection
from lib.checkpoint import ImportCheckpoint

ORACC_DIR = Path("/Volumes/Portable Storage/Glintstone/source-data/sources/ORACC")

# ORACC projects to import with metadata
ORACC_PROJECTS = {
    "dcclt": {
        "title": "Digital Corpus of Cuneiform Lexical Texts",
        "short_title": "DCCLT",
        "url": "http://oracc.org/dcclt",
    },
    "epsd2": {
        "title": "Electronic Pennsylvania Sumerian Dictionary",
        "short_title": "ePSD2",
        "url": "http://oracc.org/epsd2",
    },
    "rinap": {
        "title": "Royal Inscriptions of the Neo-Assyrian Period",
        "short_title": "RINAP",
        "url": "http://oracc.org/rinap",
    },
    "saao/saa01": {
        "title": "State Archives of Assyria Online: SAA 01",
        "short_title": "SAA 01",
        "url": "http://oracc.org/saao/saa01",
    },
    "ribo": {
        "title": "Royal Inscriptions of Babylonia Online",
        "short_title": "RIBo",
        "url": "http://oracc.org/ribo",
    },
    "riao": {
        "title": "Royal Inscriptions of Assyria Online",
        "short_title": "RIAo",
        "url": "http://oracc.org/riao",
    },
    "etcsri": {
        "title": "Electronic Text Corpus of Sumerian Royal Inscriptions",
        "short_title": "ETCSRI",
        "url": "http://oracc.org/etcsri",
    },
    "blms": {
        "title": "Bilinguals in Late Mesopotamian Scholarship",
        "short_title": "BLMS",
        "url": "http://oracc.org/blms",
    },
    "hbtin": {
        "title": "Hellenistic Babylonia: Texts, Iconography, Names",
        "short_title": "HBTIN",
        "url": "http://oracc.org/hbtin",
    },
    "dccmt": {
        "title": "Digital Corpus of Cuneiform Mathematical Texts",
        "short_title": "DCCMT",
        "url": "http://oracc.org/dccmt",
    },
    "ogsl": {
        "title": "ORACC Global Sign List",
        "short_title": "OGSL",
        "url": "http://oracc.org/ogsl",
    },
    "amgg": {
        "title": "Ancient Mesopotamian Gods and Goddesses",
        "short_title": "AMGG",
        "url": "http://oracc.org/amgg",
    },
}


class ORACCEditionImporter:
    """Imports ORACC projects as publications with artifact edition links."""

    def __init__(self, reset: bool = False):
        self.checkpoint = ImportCheckpoint("oracc_editions", reset=reset)
        self.annotation_run_ids: dict[str, int] = {}

    def run(self):
        print("=" * 60)
        print("ORACC PROJECT EDITIONS IMPORT")
        print("=" * 60)

        if self.checkpoint.is_completed():
            print("\n  Import already completed. Use --reset to reimport.")
            self.checkpoint.print_summary()
            return True

        conn = get_connection()

        try:
            # Discover available projects
            available = self._discover_projects()
            print(f"  Available ORACC projects: {len(available)}")
            self.checkpoint.set_total(len(available))

            for i, (project_key, project_dir) in enumerate(available):
                if self.checkpoint.interrupted:
                    break

                provider_name = f"ORACC/{project_key}"
                print(f"\n  [{i + 1}/{len(available)}] {project_key}...")

                run_id = self._ensure_annotation_run(conn, provider_name)
                self.annotation_run_ids[project_key] = run_id

                # Register project as publication
                pub_id = self._register_project_publication(conn, project_key, run_id)

                # Extract scholars from credits
                self._extract_scholars(conn, project_key, project_dir, pub_id)

                # Create artifact editions from catalogue
                edition_count = self._create_artifact_editions(
                    conn, project_key, project_dir, pub_id, run_id
                )

                print(f"    Editions created: {edition_count:,}")
                self.checkpoint.stats["processed"] = i + 1
                self.checkpoint.save()

            if not self.checkpoint.interrupted:
                self.checkpoint.save(completed=True)
                print("\n  Import completed successfully!")
            else:
                self.checkpoint.save(completed=False)
        finally:
            conn.close()

        self.checkpoint.print_summary()
        return not self.checkpoint.interrupted

    def _discover_projects(self) -> list[tuple[str, Path]]:
        """Find ORACC project directories with catalogue data."""
        available = []
        if not ORACC_DIR.exists():
            print(f"  ORACC directory not found: {ORACC_DIR}")
            return available

        for project_key, meta in ORACC_PROJECTS.items():
            # Handle nested projects like saao/saa01
            parts = project_key.split("/")
            project_dir = ORACC_DIR / parts[0]
            if len(parts) > 1:
                project_dir = project_dir / parts[1]

            # Check for catalogue JSON
            cat_path = project_dir / "catalogue.json"
            if not cat_path.exists():
                # Try inside json/ subdirectory
                cat_path = project_dir / "json" / "catalogue.json"

            if cat_path.exists():
                available.append((project_key, cat_path.parent))
            else:
                # Check for zip file
                zip_path = ORACC_DIR / f"{parts[0]}.zip"
                if zip_path.exists():
                    available.append((project_key, zip_path))

        return available

    def _ensure_annotation_run(
        self, conn: psycopg.Connection, provider_name: str
    ) -> int:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO annotation_runs
               (source_type, source_name, method, created_at, notes)
               VALUES (%s, %s, %s, %s, %s)
               RETURNING id""",
            (
                "import",
                provider_name,
                "import",
                datetime.now().isoformat(),
                f"ORACC project import. Provider: {provider_name}",
            ),
        )
        run_id = cursor.fetchone()[0]
        conn.commit()
        return run_id

    def _register_project_publication(
        self, conn: psycopg.Connection, project_key: str, run_id: int
    ) -> int:
        """Register an ORACC project as a digital_edition publication."""
        meta = ORACC_PROJECTS.get(project_key, {})
        bibtex_key = f"oracc:{project_key}"

        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO publications
               (bibtex_key, title, short_title, publication_type,
                url, oracc_project, authors, annotation_run_id, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT(bibtex_key) DO UPDATE SET
                   title = COALESCE(excluded.title, publications.title),
                   url = COALESCE(excluded.url, publications.url)""",
            (
                bibtex_key,
                meta.get("title", project_key),
                meta.get("short_title", project_key.upper()),
                "digital_edition",
                meta.get("url"),
                project_key,
                "ORACC Project Contributors",
                run_id,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()

        cursor.execute(
            "SELECT id FROM publications WHERE bibtex_key = %s", (bibtex_key,)
        )
        return cursor.fetchone()[0]

    def _extract_scholars(
        self, conn: psycopg.Connection, project_key: str, project_dir: Path, pub_id: int
    ):
        """Extract scholar names from ORACC credits fields."""
        cat_path = project_dir / "catalogue.json"
        if not cat_path.exists():
            return

        try:
            with open(cat_path) as f:
                catalogue = json.load(f)
        except (json.JSONDecodeError, IOError):
            return

        scholars_seen = set()
        members = catalogue.get("members", {})

        for entry in members.values():
            credits_str = entry.get("credits", "")
            if not credits_str:
                continue

            # Extract names from credits like:
            # "Created by Erle Leichty... Lemmatized by Jamie Novotny..."
            name_pattern = re.compile(r"(?:by|By)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)")
            for match in name_pattern.finditer(credits_str):
                name_raw = match.group(1)
                if name_raw not in scholars_seen:
                    scholars_seen.add(name_raw)
                    self._upsert_scholar(conn, name_raw, pub_id)

        if scholars_seen:
            print(f"    Scholars extracted: {len(scholars_seen)}")

    def _upsert_scholar(self, conn: psycopg.Connection, name_raw: str, pub_id: int):
        """Insert scholar and link to publication."""
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO scholars (name) VALUES (%s) ON CONFLICT DO NOTHING",
            (name_raw,),
        )
        cursor.execute("SELECT id FROM scholars WHERE name = %s", (name_raw,))
        row = cursor.fetchone()
        if not row:
            return

        scholar_id = row[0]

        cursor.execute(
            """INSERT INTO publication_authors
               (publication_id, scholar_id, role, position)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT(publication_id, scholar_id, role) DO NOTHING""",
            (pub_id, scholar_id, "contributor", 99),
        )
        conn.commit()

    def _create_artifact_editions(
        self,
        conn: psycopg.Connection,
        project_key: str,
        project_dir: Path,
        pub_id: int,
        run_id: int,
    ) -> int:
        """Create artifact_editions for each P-number in ORACC catalogue."""
        cat_path = project_dir / "catalogue.json"
        if not cat_path.exists():
            return 0

        try:
            with open(cat_path) as f:
                catalogue = json.load(f)
        except (json.JSONDecodeError, IOError):
            return 0

        cursor = conn.cursor()
        count = 0
        members = catalogue.get("members", {})

        try:
            for key, entry in members.items():
                p_number = entry.get("id_text", "")
                if not p_number or not p_number.startswith("P"):
                    # Try the key itself
                    if key.startswith("P"):
                        p_number = key
                    else:
                        continue

                display_name = entry.get("display_name", "") or entry.get(
                    "designation", ""
                )
                ref_str = display_name or f"{project_key}/{p_number}"

                cursor.execute(
                    """INSERT INTO artifact_editions
                       (p_number, publication_id, reference_string,
                        reference_normalized, edition_type, confidence,
                        annotation_run_id, note)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT(p_number, publication_id, reference_string) DO NOTHING""",
                    (
                        p_number,
                        pub_id,
                        ref_str,
                        ref_str.lower().strip(),
                        "full_edition",
                        0.95,
                        run_id,
                        f"ORACC/{project_key} corpus membership",
                    ),
                )
                if cursor.rowcount > 0:
                    count += 1
                    self.checkpoint.stats["inserted"] += 1

            conn.commit()
        except Exception as e:
            conn.rollback()
            self.checkpoint.record_error(project_key, str(e))

        return count


def verify():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM publications WHERE oracc_project IS NOT NULL")
    project_count = cursor.fetchone()[0]

    cursor.execute(
        """SELECT p.oracc_project, COUNT(ae.id)
           FROM artifact_editions ae
           JOIN publications p ON ae.publication_id = p.id
           WHERE p.oracc_project IS NOT NULL
           GROUP BY p.oracc_project"""
    )
    by_project = cursor.fetchall()

    cursor.execute(
        """SELECT COUNT(DISTINCT pa.scholar_id)
           FROM publication_authors pa
           JOIN publications p ON pa.publication_id = p.id
           WHERE p.oracc_project IS NOT NULL"""
    )
    scholar_count = cursor.fetchone()[0]

    conn.close()

    print(f"\n  ORACC projects registered: {project_count}")
    print(f"  Scholars from ORACC credits: {scholar_count}")
    print("\n  Editions by project:")
    for proj, count in sorted(by_project, key=lambda x: -x[1]):
        print(f"    {proj}: {count:,}")


def main():
    parser = argparse.ArgumentParser(description="Import ORACC project editions")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    if args.verify_only:
        verify()
        return

    importer = ORACCEditionImporter(reset=args.reset)
    success = importer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
