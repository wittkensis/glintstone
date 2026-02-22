#!/usr/bin/env python3
"""
Phase 8: Import scholar directory from CDLI Who's Who and Wikipedia.

- CDLI Who's Who: https://cdli.ox.ac.uk/wiki/doku.php?id=who_s_who_in_cuneiform_studies
- Wikipedia: https://en.wikipedia.org/wiki/List_of_Assyriologists

Provider: CDLI Wiki / Wikipedia

Usage:
    python 09_import_scholars_directory.py [--reset] [--verify-only]
"""

import argparse
import re
import psycopg
import sys
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).parent))

from lib.db import get_connection
from lib.name_normalizer import parse_name
from lib.checkpoint import ImportCheckpoint

CACHE_DIR = Path(__file__).parent / "_cache" / "scholars"

WHOS_WHO_URL = "https://cdli.ox.ac.uk/wiki/doku.php?id=who_s_who_in_cuneiform_studies"
WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/List_of_Assyriologists"


class ScholarDirectoryImporter:
    def __init__(self, reset: bool = False):
        self.checkpoint = ImportCheckpoint("scholars_directory", reset=reset)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def run(self):
        print("=" * 60)
        print("SCHOLAR DIRECTORY IMPORT")
        print("=" * 60)

        if self.checkpoint.is_completed():
            print("\n  Import already completed. Use --reset to reimport.")
            return True

        conn = get_connection()

        try:
            # Import Who's Who
            print("\n  Importing CDLI Who's Who...")
            ww_count = self._import_whos_who(conn)
            print(f"    Scholars from Who's Who: {ww_count:,}")

            # Import Wikipedia list
            if not self.checkpoint.interrupted:
                print("\n  Importing Wikipedia Assyriologists list...")
                wp_count = self._import_wikipedia(conn)
                print(f"    Scholars from Wikipedia: {wp_count:,}")

            if not self.checkpoint.interrupted:
                self.checkpoint.save(completed=True)
                print("\n  Import completed!")
        finally:
            conn.close()

        self.checkpoint.print_summary()
        return not self.checkpoint.interrupted

    def _fetch_page(self, url: str, cache_name: str) -> str:
        """Fetch a web page with local caching."""
        cache_path = CACHE_DIR / f"{cache_name}.html"

        if cache_path.exists():
            return cache_path.read_text(encoding="utf-8", errors="replace")

        try:
            with urlopen(url, timeout=30) as resp:
                html = resp.read().decode("utf-8", errors="replace")
                cache_path.write_text(html)
                return html
        except Exception as e:
            print(f"    Error fetching {url}: {e}")
            return ""

    def _import_whos_who(self, conn: psycopg.Connection) -> int:
        """Parse CDLI Who's Who wiki page for scholar names and dates."""
        html = self._fetch_page(WHOS_WHO_URL, "whos_who")
        if not html:
            return 0

        cursor = conn.cursor()
        count = 0

        # Extract scholar entries from wiki content
        # Typical format: <a>Name</a> (birth-death) - description
        # or just linked names in alphabetical lists
        name_pattern = re.compile(
            r"<a[^>]*>([A-Z][^<]{2,50})</a>\s*" r"(?:\((\d{4})\s*[-–]\s*(\d{4})?\))?",
        )

        for match in name_pattern.finditer(html):
            name_raw = match.group(1).strip()
            birth = match.group(2)

            # Skip non-person entries
            if any(
                skip in name_raw.lower()
                for skip in [
                    "university",
                    "museum",
                    "institute",
                    "project",
                    "who's who",
                ]
            ):
                continue

            parsed = parse_name(name_raw)
            if not parsed.surname:
                continue

            # Upsert scholar
            cursor.execute(
                """INSERT INTO scholars (name, active_since)
                   VALUES (%s, %s)
                   ON CONFLICT DO NOTHING""",
                (name_raw, birth),
            )
            if cursor.rowcount > 0:
                count += 1

        conn.commit()
        self.checkpoint.stats["inserted"] += count
        return count

    def _import_wikipedia(self, conn: psycopg.Connection) -> int:
        """Parse Wikipedia List of Assyriologists for names and Wikidata links."""
        html = self._fetch_page(WIKIPEDIA_URL, "wikipedia_assyriologists")
        if not html:
            return 0

        cursor = conn.cursor()
        count = 0

        # Wikipedia list items typically: <li><a href="/wiki/Name" title="Name">Name</a> (dates)</li>
        entry_pattern = re.compile(
            r'<li><a\s+href="/wiki/([^"]+)"[^>]*>([^<]+)</a>'
            r"\s*\((\d{4})\s*[-–]\s*(\d{4})?\)?",
        )

        for match in entry_pattern.finditer(html):
            name_raw = match.group(2).strip()
            birth = match.group(3)

            parsed = parse_name(name_raw)
            if not parsed.surname:
                continue

            # Upsert scholar
            cursor.execute(
                """INSERT INTO scholars (name, active_since)
                   VALUES (%s, %s)
                   ON CONFLICT DO NOTHING""",
                (name_raw, birth),
            )
            if cursor.rowcount > 0:
                count += 1

            # Try to add Wikidata authority link
            # (Would need Wikidata API call to get QID from wiki slug)
            # Deferred: authority_links population requires entity_id

        conn.commit()
        self.checkpoint.stats["inserted"] += count
        return count


def verify():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM scholars")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM scholars WHERE orcid IS NOT NULL")
    with_orcid = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM scholars WHERE active_since IS NOT NULL")
    with_dates = c.fetchone()[0]
    conn.close()

    print(f"\n  Total scholars: {total:,}")
    print(f"  With ORCID: {with_orcid:,}")
    print(f"  With dates: {with_dates:,}")


def main():
    parser = argparse.ArgumentParser(description="Import scholar directories")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    if args.verify_only:
        verify()
        return

    importer = ScholarDirectoryImporter(reset=args.reset)
    success = importer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
