"""Semantic Scholar API — on-demand citation graph lookup."""

import logging
import subprocess
import json
from time import time

log = logging.getLogger(__name__)

_BASE = "https://api.semanticscholar.org/graph/v1"
_CACHE: dict[str, tuple[float, list]] = {}  # doi → (timestamp, citations)
_TTL = 3600  # 1 hour


def get_citation_graph(doi: str, limit: int = 20) -> dict:
    """Fetch papers that cite the given DOI from Semantic Scholar.

    Returns {citations: [...], total: N, source: "semantic_scholar"}.
    Uses subprocess curl (macOS SSL workaround) with in-memory cache.
    """
    if not doi:
        return {"citations": [], "total": 0, "source": "semantic_scholar"}

    # Check cache
    cached = _CACHE.get(doi)
    if cached and (time() - cached[0]) < _TTL:
        return {
            "citations": cached[1],
            "total": len(cached[1]),
            "source": "semantic_scholar",
        }

    url = f"{_BASE}/paper/DOI:{doi}/citations?fields=title,authors,year,externalIds&limit={limit}"

    try:
        result = subprocess.run(
            ["curl", "-s", "-f", "--max-time", "5", url],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if result.returncode != 0:
            log.warning("S2 API error for DOI %s: exit %d", doi, result.returncode)
            return {
                "citations": [],
                "total": 0,
                "source": "semantic_scholar",
                "error": "api_error",
            }

        data = json.loads(result.stdout)
        citations = []
        for item in data.get("data", []):
            citing = item.get("citingPaper", {})
            if not citing.get("title"):
                continue
            citations.append(
                {
                    "title": citing["title"],
                    "year": citing.get("year"),
                    "authors": [
                        a.get("name", "") for a in citing.get("authors", [])[:4]
                    ],
                    "doi": (citing.get("externalIds") or {}).get("DOI"),
                }
            )

        _CACHE[doi] = (time(), citations)
        return {
            "citations": citations,
            "total": len(citations),
            "source": "semantic_scholar",
        }

    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        log.warning("S2 citation fetch failed for DOI %s: %s", doi, e)
        return {
            "citations": [],
            "total": 0,
            "source": "semantic_scholar",
            "error": str(e),
        }
