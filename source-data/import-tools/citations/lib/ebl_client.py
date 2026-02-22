#!/usr/bin/env python3
"""
eBL (Electronic Babylonian Literature) API client.

Fetches fragment-level bibliography data from the eBL API.
All data sourced from eBL must carry provider attribution.

Provider: eBL - Electronic Babylonian Literature
Institution: LMU Munich
URL: https://www.ebl.lmu.de/
"""

import json
import time
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

EBL_BASE_URL = "https://www.ebl.lmu.de/api"
CACHE_DIR = Path(__file__).parent.parent / "_cache" / "ebl"

REQUEST_DELAY_SECONDS = 1.0

PROVIDER_NAME = "eBL - Electronic Babylonian Literature"
PROVIDER_INSTITUTION = "LMU Munich"

# eBL ReferenceType -> v2 edition_type mapping
REFERENCE_TYPE_MAP = {
    "EDITION": "full_edition",
    "DISCUSSION": "commentary",
    "COPY": "hand_copy",
    "PHOTO": "photograph_only",
    "TRANSLATION": "translation_only",
    "ARCHAEOLOGY": "catalog_entry",
    "ACQUISITION": "catalog_entry",
    "SEAL": "catalog_entry",
}


class EBLClient:
    """eBL REST API client with local cache and provider attribution."""

    def __init__(self, api_token: Optional[str] = None):
        """
        Args:
            api_token: Optional API token for authenticated access.
                       Set to None to test unauthenticated endpoints first.
        """
        self.api_token = api_token
        self._last_request_time = 0.0
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _rate_limit(self):
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < REQUEST_DELAY_SECONDS:
            time.sleep(REQUEST_DELAY_SECONDS - elapsed)
        self._last_request_time = time.time()

    def _make_request(self, url: str) -> Optional[dict]:
        """Make authenticated API request."""
        self._rate_limit()
        headers = {"Accept": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            if e.code == 401:
                print("    eBL API: Authentication required. Set api_token.")
            elif e.code == 403:
                print("    eBL API: Access forbidden. Check API permissions.")
            elif e.code == 429:
                print("    eBL API: Rate limited. Waiting 30s...")
                time.sleep(30)
                return self._make_request(url)
            else:
                print(f"    eBL API HTTP error {e.code}: {url}")
            return None
        except (URLError, TimeoutError) as e:
            print(f"    eBL API network error: {e}")
            return None

    def fetch_fragment_bibliography(self, fragment_number: str) -> Optional[list]:
        """
        Fetch bibliography entries for a specific fragment.

        Args:
            fragment_number: eBL fragment identifier (e.g., "K.1")

        Returns:
            List of bibliography reference dicts, or None on error.
        """
        safe_name = fragment_number.replace("/", "_").replace(" ", "_")
        cache_path = CACHE_DIR / f"frag_{safe_name}_bib.json"

        if cache_path.exists():
            with open(cache_path) as f:
                return json.load(f)

        url = f"{EBL_BASE_URL}/fragments/{fragment_number}/bibliography"
        data = self._make_request(url)

        if data is not None:
            cache_path.write_text(json.dumps(data, indent=2))

        return data

    def parse_bibliography_entry(self, entry: dict) -> dict:
        """
        Transform an eBL bibliography entry to v2 schema fields.

        eBL uses CSL-JSON internally. A bibliography reference includes:
        - reference: CSL-JSON bibliographic record
        - type: ReferenceType enum (EDITION, DISCUSSION, COPY, etc.)
        - pages: page range string
        - notes: freetext notes
        - linesCited: array of line references
        """
        ref = entry.get("reference", {})
        ref_type = entry.get("type", "DISCUSSION")

        # Extract CSL-JSON fields
        authors = []
        for author in ref.get("author", []):
            name_parts = []
            if author.get("given"):
                name_parts.append(author["given"])
            if author.get("family"):
                name_parts.append(author["family"])
            authors.append(" ".join(name_parts))

        # Extract year from date-parts
        year = None
        issued = ref.get("issued", {})
        date_parts = issued.get("date-parts", [[]])
        if date_parts and date_parts[0]:
            year = str(date_parts[0][0])

        return {
            "title": ref.get("title", ""),
            "authors_raw": "; ".join(authors),
            "year": year,
            "doi": ref.get("DOI"),
            "publication_type": self._csl_type_to_pub_type(ref.get("type", "")),
            "edition_type": REFERENCE_TYPE_MAP.get(ref_type, "catalog_entry"),
            "pages": entry.get("pages", ""),
            "notes": entry.get("notes", ""),
            "lines_cited": entry.get("linesCited", []),
            "container_title": ref.get("container-title", ""),
            "volume": ref.get("volume"),
            "issue": ref.get("issue"),
            "publisher": ref.get("publisher"),
            "provider": PROVIDER_NAME,
        }

    @staticmethod
    def _csl_type_to_pub_type(csl_type: str) -> str:
        """Map CSL-JSON type to v2 publication_type."""
        mapping = {
            "article-journal": "journal_article",
            "book": "monograph",
            "chapter": "chapter",
            "paper-conference": "conference_paper",
            "thesis": "thesis",
            "report": "report",
        }
        return mapping.get(csl_type, "other")

    def test_connection(self) -> bool:
        """Test if the eBL API is accessible."""
        # Try a known fragment
        result = self._make_request(f"{EBL_BASE_URL}/fragments/K.1")
        if result is not None:
            print("  eBL API: Connection successful")
            return True
        print("  eBL API: Connection failed")
        return False
