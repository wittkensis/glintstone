#!/usr/bin/env python3
"""
Phase 7 (Optional): Enrich with Semantic Scholar citation graphs.

For each publication with a DOI, fetches citation/reference data
from Semantic Scholar API.

Provider: Semantic Scholar
Rate limit: 100 requests / 5 minutes

Usage:
    python 08_enrich_semantic_scholar.py [--reset] [--verify-only]
"""

import argparse
import json
import psycopg
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.checkpoint import ImportCheckpoint
from lib.db import get_connection

CACHE_DIR = Path(__file__).parent / "_cache" / "semantic_scholar"

PROVIDER_NAME = "Semantic Scholar"
S2_BASE = "https://api.semanticscholar.org/graph/v1"
REQUESTS_PER_WINDOW = 95  # Stay under 100/5min limit
WINDOW_SECONDS = 300


class SemanticScholarEnricher:
    def __init__(self, reset: bool = False):
        self.checkpoint = ImportCheckpoint("semantic_scholar", reset=reset)
        self._request_count = 0
        self._window_start = time.time()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def run(self):
        print("=" * 60)
        print("SEMANTIC SCHOLAR CITATION ENRICHMENT")
        print(f"  Provider: {PROVIDER_NAME}")
        print(f"  Rate limit: {REQUESTS_PER_WINDOW} requests / {WINDOW_SECONDS}s")
        print("=" * 60)

        if self.checkpoint.is_completed():
            print("\n  Enrichment already completed. Use --reset to re-run.")
            return True

        conn = get_connection()

        try:
            # Get publications with DOIs
            cursor = conn.cursor()
            cursor.execute("SELECT id, doi FROM publications WHERE doi IS NOT NULL")
            pubs_with_doi = cursor.fetchall()
            print(f"  Publications with DOI: {len(pubs_with_doi):,}")

            self.checkpoint.set_total(len(pubs_with_doi))

            for i, (pub_id, doi) in enumerate(pubs_with_doi):
                if self.checkpoint.interrupted:
                    break

                citations = self._fetch_citations(doi)
                if citations is not None:
                    self._store_citations(conn, pub_id, doi, citations)

                self.checkpoint.stats["processed"] = i + 1
                if (i + 1) % 50 == 0:
                    self.checkpoint.save()
                    self.checkpoint.print_progress(i + 1, len(pubs_with_doi))

            if not self.checkpoint.interrupted:
                self.checkpoint.save(completed=True)
                print("\n  Enrichment completed!")
            else:
                self.checkpoint.save(completed=False)
        finally:
            conn.close()

        self.checkpoint.print_summary()
        return not self.checkpoint.interrupted

    def _rate_limit(self):
        """Enforce Semantic Scholar rate limits."""
        self._request_count += 1
        if self._request_count >= REQUESTS_PER_WINDOW:
            elapsed = time.time() - self._window_start
            if elapsed < WINDOW_SECONDS:
                wait = WINDOW_SECONDS - elapsed + 5
                print(f"\n    Rate limit reached. Waiting {wait:.0f}s...")
                time.sleep(wait)
            self._request_count = 0
            self._window_start = time.time()

    def _fetch_citations(self, doi: str) -> dict | None:
        """Fetch citation data from Semantic Scholar."""
        cache_path = CACHE_DIR / f"{doi.replace('/', '_')}.json"

        if cache_path.exists():
            with open(cache_path) as f:
                return json.load(f)

        self._rate_limit()

        url = f"{S2_BASE}/paper/DOI:{doi}?fields=citationCount"

        try:
            result = subprocess.run(
                [
                    "curl",
                    "-sL",
                    "-H",
                    "Accept: application/json",
                    "--max-time",
                    "30",
                    url,
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return None

            if not result.stdout.strip():
                return None

            data = json.loads(result.stdout)

            # Handle HTTP errors encoded in response
            if "error" in data or "message" in data:
                msg = data.get("message", data.get("error", ""))
                if "404" in str(msg) or "not found" in str(msg).lower():
                    return None
                if "429" in str(msg) or "rate" in str(msg).lower():
                    time.sleep(60)
                    return self._fetch_citations(doi)
                return None

            cache_path.write_text(json.dumps(data, indent=2))
            return data
        except json.JSONDecodeError:
            return None
        except Exception:
            return None

    def _store_citations(
        self, conn: psycopg.Connection, pub_id: int, doi: str, data: dict
    ):
        """Store citation count on the publication."""
        citation_count = data.get("citationCount")
        if citation_count is not None:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE publications SET cited_by_count = %s WHERE id = %s",
                    (citation_count, pub_id),
                )
            conn.commit()
        self.checkpoint.stats["updated"] = self.checkpoint.stats.get("updated", 0) + 1


def verify():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM publications WHERE doi IS NOT NULL")
    doi_count = c.fetchone()[0]
    conn.close()
    print(f"\n  Publications with DOI (S2 eligible): {doi_count:,}")
    print(f"  Cache files: {len(list(CACHE_DIR.glob('*.json'))):,}")


def main():
    parser = argparse.ArgumentParser(description="Enrich via Semantic Scholar")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    if args.verify_only:
        verify()
        return

    enricher = SemanticScholarEnricher(reset=args.reset)
    success = enricher.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
