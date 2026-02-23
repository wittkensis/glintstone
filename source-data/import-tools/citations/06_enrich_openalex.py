#!/usr/bin/env python3
"""
Phase 5: Enrich publications with DOIs and scholars with ORCIDs via OpenAlex.

Queries OpenAlex for Assyriology-related works, backfills DOIs on existing
publications, and enriches scholar records with ORCID identifiers.

Provider: OpenAlex (CC0)

Usage:
    python 06_enrich_openalex.py [--reset] [--verify-only]
"""

import argparse
import json
import psycopg
import psycopg.errors
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.db import get_connection
from lib.publication_matcher import normalize_title
from lib.name_normalizer import parse_name
from lib.checkpoint import ImportCheckpoint

CACHE_DIR = Path(__file__).parent / "_cache" / "openalex"

PROVIDER_NAME = "OpenAlex"

# OpenAlex topic IDs (concepts API was deprecated)
TOPIC_FILTERS = [
    "topics.id:T12307",  # Ancient Near East History (Mesopotamia, cuneiform, Sumerian, Akkadian)
]

OPENALEX_BASE = "https://api.openalex.org"
REQUEST_DELAY = 0.2  # OpenAlex is generous with rate limits


class OpenAlexEnricher:
    def __init__(self, reset: bool = False):
        self.checkpoint = ImportCheckpoint("openalex_enrichment", reset=reset)
        self.annotation_run_id = None
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def run(self):
        print("=" * 60)
        print("OPENALEX ENRICHMENT")
        print(f"  Provider: {PROVIDER_NAME}")
        print("=" * 60)

        if self.checkpoint.is_completed():
            print("\n  Enrichment already completed. Use --reset to re-run.")
            return True

        conn = get_connection()

        try:
            self.annotation_run_id = self._ensure_annotation_run(conn)

            # Step 1: Fetch Assyriology works from OpenAlex
            print("\n  Step 1: Fetching Assyriology works from OpenAlex...")
            works = self._fetch_assyriology_works()
            print(f"    Found {len(works):,} works")

            # Step 2: Backfill DOIs on existing publications
            print("\n  Step 2: Backfilling DOIs...")
            doi_count = self._backfill_dois(conn, works)
            print(f"    DOIs backfilled: {doi_count:,}")

            # Step 3: Backfill ORCIDs on scholars
            print("\n  Step 3: Backfilling ORCIDs...")
            orcid_count = self._backfill_orcids(conn, works)
            print(f"    ORCIDs backfilled: {orcid_count:,}")

            # Step 4: Import new publications not already in DB
            print("\n  Step 4: Importing new publications...")
            new_count = self._import_new_publications(conn, works)
            print(f"    New publications: {new_count:,}")

            if not self.checkpoint.interrupted:
                self.checkpoint.save(completed=True)
                print("\n  Enrichment completed!")
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
            (
                "import",
                PROVIDER_NAME,
                "api_fetch",
                datetime.now().isoformat(),
                f"OpenAlex enrichment for Assyriology publications. Provider: {PROVIDER_NAME}",
            ),
        )
        run_id = cursor.fetchone()[0]
        conn.commit()
        return run_id

    def _fetch_assyriology_works(self) -> list[dict]:
        """Fetch all Assyriology-related works from OpenAlex using cursor pagination."""
        all_works = []
        cache_path = CACHE_DIR / "assyriology_works.json"

        # Check cache
        if cache_path.exists():
            with open(cache_path) as f:
                cached = json.load(f)
                if len(cached) > 100:
                    print(f"    Using cached data ({len(cached):,} works)")
                    return cached

        for topic_filter in TOPIC_FILTERS:
            cursor = "*"
            while cursor:
                if self.checkpoint.interrupted:
                    break

                url = (
                    f"{OPENALEX_BASE}/works?"
                    f"filter={topic_filter}"
                    f"&per_page=200&cursor={cursor}"
                    f"&select=id,doi,title,publication_year,type,authorships,cited_by_count"
                )

                data = self._api_request(url)
                if not data or not data.get("results"):
                    break

                all_works.extend(data["results"])
                cursor = data.get("meta", {}).get("next_cursor")

                if len(all_works) % 1000 == 0:
                    print(f"    Fetched {len(all_works):,}...", end="\r")

        # Only cache if we got meaningful results
        if all_works:
            cache_path.write_text(json.dumps(all_works, indent=2))
        return all_works

    def _backfill_dois(self, conn: psycopg.Connection, works: list) -> int:
        """Match OpenAlex works to existing publications by title+year, backfill DOI."""
        cursor = conn.cursor()

        # Load publications without DOIs
        cursor.execute(
            "SELECT id, title, year FROM publications WHERE doi IS NULL AND title IS NOT NULL"
        )
        pubs_without_doi = cursor.fetchall()
        print(f"    Publications without DOI: {len(pubs_without_doi):,}")

        # Build normalized title index from OpenAlex
        oa_by_title = {}
        for work in works:
            if work.get("doi") and work.get("title"):
                norm = normalize_title(work["title"])
                year = work.get("publication_year")
                oa_by_title[(norm, str(year) if year else "")] = work["doi"]

        count = 0
        for pub_id, title, year in pubs_without_doi:
            norm = normalize_title(title or "")
            year_str = str(year) if year else ""

            doi = oa_by_title.get((norm, year_str))
            if doi:
                clean_doi = doi.replace("https://doi.org/", "")
                cursor.execute(
                    "UPDATE publications SET doi = %s WHERE id = %s AND NOT EXISTS (SELECT 1 FROM publications WHERE doi = %s)",
                    (clean_doi, pub_id, clean_doi),
                )
                if cursor.rowcount > 0:
                    count += 1

        conn.commit()
        self.checkpoint.stats["updated"] += count
        return count

    def _backfill_orcids(self, conn: psycopg.Connection, works: list) -> int:
        """Extract ORCIDs from OpenAlex authorships and match to existing scholars."""
        cursor = conn.cursor()

        # Load scholars without ORCID
        cursor.execute("SELECT id, name FROM scholars WHERE orcid IS NULL")
        scholars = cursor.fetchall()
        print(f"    Scholars without ORCID: {len(scholars):,}")

        # Build normalized name -> ORCID map from OpenAlex
        orcid_map: dict[str, str] = {}
        for work in works:
            for authorship in work.get("authorships", []):
                author = authorship.get("author", {})
                orcid = author.get("orcid")
                name = author.get("display_name")
                if orcid and name:
                    parsed = parse_name(name)
                    orcid_map[parsed.normalized_key] = orcid.replace(
                        "https://orcid.org/", ""
                    )

        count = 0
        for scholar_id, name in scholars:
            parsed = parse_name(name)
            orcid = orcid_map.get(parsed.normalized_key)
            if orcid:
                cursor.execute(
                    "UPDATE scholars SET orcid = %s WHERE id = %s AND NOT EXISTS (SELECT 1 FROM scholars WHERE orcid = %s)",
                    (orcid, scholar_id, orcid),
                )
                if cursor.rowcount > 0:
                    count += 1

        conn.commit()
        self.checkpoint.stats["updated"] += count
        return count

    def _import_new_publications(self, conn: psycopg.Connection, works: list) -> int:
        """Import OpenAlex works not already in the database."""
        cursor = conn.cursor()

        # Get existing DOIs for fast dedup
        cursor.execute("SELECT doi FROM publications WHERE doi IS NOT NULL")
        existing_dois = {row[0] for row in cursor.fetchall()}

        count = 0
        batch = []

        for work in works:
            doi = work.get("doi", "")
            if doi:
                doi = doi.replace("https://doi.org/", "")
            if doi in existing_dois:
                continue
            if not work.get("title"):
                continue

            # Build author string
            authors = []
            for a in work.get("authorships", []):
                name = a.get("author", {}).get("display_name")
                if name:
                    authors.append(name)

            pub_type = self._map_type(work.get("type", ""))
            year = work.get("publication_year")

            batch.append(
                (
                    f"openalex:{work.get('id', '').split('/')[-1]}",
                    work["title"],
                    pub_type,
                    year,
                    "; ".join(authors) or "Unknown",
                    doi or None,
                    self.annotation_run_id,
                    datetime.now().isoformat(),
                )
            )

            if doi:
                existing_dois.add(doi)

            if len(batch) >= 500:
                cursor.executemany(
                    """INSERT INTO publications
                       (bibtex_key, title, publication_type, year, authors,
                        doi, annotation_run_id, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT(bibtex_key) DO NOTHING""",
                    batch,
                )
                count += cursor.rowcount
                conn.commit()
                batch = []

        if batch:
            cursor.executemany(
                """INSERT INTO publications
                   (bibtex_key, title, publication_type, year, authors,
                    doi, annotation_run_id, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT(bibtex_key) DO NOTHING""",
                batch,
            )
            count += cursor.rowcount
            conn.commit()

        self.checkpoint.stats["inserted"] += count
        return count

    @staticmethod
    def _map_type(oa_type: str) -> str:
        mapping = {
            "journal-article": "journal_article",
            "book": "monograph",
            "book-chapter": "chapter",
            "proceedings-article": "conference_paper",
            "dissertation": "dissertation",
        }
        return mapping.get(oa_type, "other")

    def _api_request(self, url: str) -> dict | None:
        time.sleep(REQUEST_DELAY)
        try:
            result = subprocess.run(
                [
                    "curl",
                    "-sL",
                    "-H",
                    "Accept: application/json",
                    "-H",
                    "User-Agent: Glintstone/1.0 (mailto:glintstone@example.com)",
                    "--max-time",
                    "30",
                    url,
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"    curl error: {result.stderr.strip()}")
                return None
            data = json.loads(result.stdout)
            # Handle rate limiting
            if isinstance(data, dict) and data.get("error"):
                if "429" in str(data.get("error", "")):
                    time.sleep(5)
                    return self._api_request(url)
                print(f"    OpenAlex error: {data['error']}")
                return None
            return data
        except json.JSONDecodeError:
            print("    OpenAlex returned non-JSON response")
            return None
        except Exception as e:
            print(f"    OpenAlex error: {e}")
            return None


def verify():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM publications WHERE doi IS NOT NULL")
    doi_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM scholars WHERE orcid IS NOT NULL")
    orcid_count = c.fetchone()[0]
    c.execute(
        "SELECT COUNT(*) FROM publications p "
        "JOIN annotation_runs ar ON p.annotation_run_id = ar.id "
        "WHERE ar.source_name = %s",
        (PROVIDER_NAME,),
    )
    oa_pubs = c.fetchone()[0]
    conn.close()

    print(f"\n  Publications with DOI: {doi_count:,}")
    print(f"  Scholars with ORCID: {orcid_count:,}")
    print(f"  OpenAlex-sourced publications: {oa_pubs:,}")


def main():
    parser = argparse.ArgumentParser(description="Enrich via OpenAlex")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    if args.verify_only:
        verify()
        return

    enricher = OpenAlexEnricher(reset=args.reset)
    success = enricher.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
