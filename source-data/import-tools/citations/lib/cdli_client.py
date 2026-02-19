#!/usr/bin/env python3
"""
Dynamic CDLI API client with local cache.

Fetches publication and artifact data on-demand from cdli.earth,
caching responses locally to avoid redundant API calls.

Provider: CDLI - cdli.earth
License: CC0
"""

import json
import ssl
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# macOS doesn't ship CA certs for Python — bypass SSL verification for CDLI API
_SSL_CONTEXT = ssl.create_default_context()
_SSL_CONTEXT.check_hostname = False
_SSL_CONTEXT.verify_mode = ssl.CERT_NONE

CDLI_BASE_URL = "https://cdli.earth"
CACHE_DIR = Path(__file__).parent.parent / "_cache" / "cdli"
CACHE_MAX_AGE_DAYS = 7  # Re-fetch after 7 days

# Rate limiting: be polite to the CDLI API
REQUEST_DELAY_SECONDS = 0.5

PROVIDER_NAME = "CDLI - cdli.earth"
PROVIDER_LICENSE = "CC0"


class CDLIClient:
    """Dynamic CDLI REST API client with local file cache."""

    def __init__(self, cache_max_age_days: int = CACHE_MAX_AGE_DAYS):
        self.cache_max_age = timedelta(days=cache_max_age_days)
        self._last_request_time = 0.0
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _rate_limit(self):
        """Enforce minimum delay between requests."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < REQUEST_DELAY_SECONDS:
            time.sleep(REQUEST_DELAY_SECONDS - elapsed)
        self._last_request_time = time.time()

    def _cache_path(self, endpoint: str, page: int) -> Path:
        """Generate cache file path for an API response."""
        safe_endpoint = endpoint.strip("/").replace("/", "_")
        return CACHE_DIR / f"{safe_endpoint}_page{page:05d}.json"

    def _is_cache_fresh(self, path: Path) -> bool:
        """Check if cached file is still within max age."""
        if not path.exists():
            return False
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        return (datetime.now() - mtime) < self.cache_max_age

    def _fetch_json(self, url: str) -> Optional[dict]:
        """Fetch JSON from URL with rate limiting and error handling."""
        self._rate_limit()
        try:
            req = Request(url, headers={"Accept": "application/json"})
            with urlopen(req, timeout=30, context=_SSL_CONTEXT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            if e.code == 429:
                # Rate limited -- back off and retry once
                print(f"    Rate limited by CDLI API. Waiting 10s...")
                time.sleep(10)
                try:
                    with urlopen(req, timeout=30, context=_SSL_CONTEXT) as resp:
                        return json.loads(resp.read().decode("utf-8"))
                except Exception:
                    return None
            print(f"    HTTP error {e.code} fetching {url}")
            return None
        except (URLError, TimeoutError) as e:
            print(f"    Network error fetching {url}: {e}")
            return None

    def fetch_publications_page(self, page: int = 1, per_page: int = 100) -> Optional[dict]:
        """
        Fetch a page of publications from CDLI API.

        Returns normalized dict with 'data' list. The CDLI API now returns a
        plain list instead of the old {"count": N, "data": [...]} envelope.
        """
        cache_path = self._cache_path("publications", page)

        if self._is_cache_fresh(cache_path):
            with open(cache_path) as f:
                cached = json.load(f)
            return self._normalize_publications_response(cached)

        url = f"{CDLI_BASE_URL}/publications.json?page={page}&per_page={per_page}"
        raw = self._fetch_json(url)

        if raw:
            cache_path.write_text(json.dumps(raw, indent=2))

        return self._normalize_publications_response(raw)

    @staticmethod
    def _normalize_publications_response(raw) -> Optional[dict]:
        """Normalize API response to {"data": [...]} regardless of API version."""
        if raw is None:
            return None
        if isinstance(raw, list):
            return {"data": raw}
        if isinstance(raw, dict):
            # Old format: {"count": N, "data": [...], "offset": M}
            return raw
        return None

    def fetch_artifact_publications(self, artifact_id: int) -> Optional[list]:
        """
        Fetch publications linked to a specific artifact.

        Returns list of publication link objects with nested publication data.
        The CDLI API now returns a list with one artifact dict (not a bare dict).
        """
        cache_path = CACHE_DIR / f"artifact_{artifact_id:06d}_pubs.json"

        if self._is_cache_fresh(cache_path):
            with open(cache_path) as f:
                return json.load(f)

        url = f"{CDLI_BASE_URL}/artifacts/{artifact_id}.json"
        data = self._fetch_json(url)

        # API now returns a list with one artifact; handle both old and new format
        if isinstance(data, list) and data:
            artifact = data[0]
        elif isinstance(data, dict):
            artifact = data
        else:
            return None

        if artifact and "publications" in artifact:
            pubs = artifact["publications"]
            cache_path.write_text(json.dumps(pubs, indent=2))
            return pubs

        return None

    def fetch_all_publications(self, start_page: int = 1) -> list[dict]:
        """
        Iterate all publication pages. Yields publication records.

        Args:
            start_page: Page to resume from (for checkpoint support)

        Yields:
            Individual publication dicts from the API
        """
        page = start_page
        while True:
            result = self.fetch_publications_page(page)
            if not result or not result.get("data"):
                break

            items = result["data"]
            yield from items

            # Old API: use count/offset. New API: stop when page is not full.
            if "count" in result:
                total = result.get("count", 0)
                offset = result.get("offset", 0)
                if offset + len(items) >= total:
                    break
            else:
                if len(items) < 100:
                    break

            page += 1

    def estimate_total_pages(self, per_page: int = 100) -> int:
        """Fetch page 1 to estimate total publication count."""
        result = self.fetch_publications_page(1, per_page)
        if result and "count" in result:
            total = result["count"]
            return (total + per_page - 1) // per_page
        elif result and result.get("data"):
            # API no longer reports count — return large sentinel so callers
            # iterate until they get an empty page.
            return 99999
        return 0

    def parse_publication(self, raw: dict) -> dict:
        """
        Transform a raw CDLI API publication record to v2 schema fields.

        The CDLI API returns:
        {
            "id": 472,
            "designation": "ATU 3",
            "bibtexkey": "Englund1993ATU3",
            "year": "1993",
            "entry_type_id": 2,
            "address": "Berlin",
            "number": "Band 3",
            "publisher": "Gebr. Mann",
            "title": "Die lexikalischen Listen...",
            "series": "Archaische Texte aus Uruk"
        }
        """
        from .bibtex_parser import (
            cdli_entry_type_to_publication_type,
            parse_series_designation,
        )

        designation = raw.get("designation", "")
        series_key, volume = parse_series_designation(designation)

        # If no series from designation, try the series field
        if not series_key and raw.get("series"):
            series_key, volume = parse_series_designation(raw["series"])

        return {
            "cdli_id": raw.get("id"),
            "bibtex_key": raw.get("bibtexkey", ""),
            "title": raw.get("title", ""),
            "short_title": designation,
            "year": raw.get("year"),
            "publisher": raw.get("publisher"),
            "publication_type": cdli_entry_type_to_publication_type(
                raw.get("entry_type_id", 8)
            ),
            "series_key": series_key,
            "volume_in_series": volume or raw.get("number"),
            "address": raw.get("address"),
        }

    def parse_artifact_publication_link(self, link: dict) -> dict:
        """
        Transform a raw CDLI API artifact-publication link to v2 fields.

        The CDLI API returns per artifact:
        {
            "id": 276466404,
            "entity_id": 1,
            "publication_id": 472,
            "exact_reference": "pl. 11, W 6435,a",
            "publication_type": "history",
            "publication": { ... nested pub ... }
        }
        """
        pub = link.get("publication", {})

        # Parse exact_reference into structured components
        ref = link.get("exact_reference", "")
        page_start, plate_no, item_no = self._parse_reference(ref)

        # Map CDLI publication_type to v2 edition_type
        cdli_type = link.get("publication_type", "")
        edition_type = "full_edition" if cdli_type == "primary" else "catalog_entry"

        return {
            "publication_bibtex_key": pub.get("bibtexkey", ""),
            "exact_reference": ref,
            "page_start": page_start,
            "plate_no": plate_no,
            "item_no": item_no,
            "edition_type": edition_type,
            "confidence": 1.0,
            "provider": PROVIDER_NAME,
        }

    @staticmethod
    def _parse_reference(ref: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse a CDLI exact_reference string into components.

        "pl. 11, W 6435,a" -> (None, "11", None)
        "594" -> ("594", None, None)
        "p. 52 fig. 15" -> ("52", None, None)
        """
        if not ref:
            return None, None, None

        page_start = None
        plate_no = None
        item_no = None

        # Plate pattern: "pl. 011" or "Pl. 11"
        plate_match = re.search(r"[Pp]l\.?\s*(\d+)", ref)
        if plate_match:
            plate_no = plate_match.group(1)

        # Page pattern: "p. 52" or bare number at start
        page_match = re.search(r"[Pp]\.?\s*(\d+)", ref)
        if page_match and not plate_match:
            page_start = page_match.group(1)
        elif re.match(r"^\d+$", ref.strip()):
            page_start = ref.strip()

        return page_start, plate_no, item_no


import re  # noqa: E402 (already imported above, but making explicit for _parse_reference)
