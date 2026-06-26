"""Thin HTTP client the ingestion layer uses to record artifact-image
locations through the API rather than touching the database directly.

This exists to honor Glintstone's two-tier rule: ingestion workers persist
through the API (``api/``) over HTTP, never by opening a database connection
of their own. The CDLI image scraper (``ingestion/connectors/cdli_images.py``)
uses ``record_image_path`` to register each downloaded file's on-disk location.

Design notes
------------
- We shell out to ``curl`` rather than use ``requests``/``httpx`` because of
  the documented macOS SSL flakiness (see CLAUDE.md non-negotiable). For a
  plain-HTTP localhost API call this is overkill, but keeping one transport
  for the whole ingestion layer avoids surprises when the API base URL points
  at an HTTPS endpoint.
- ``record_image_path`` is best-effort and *never* raises on a transport or
  HTTP error. The scraper's source of truth for resumability is the local job
  queue + the files on disk; the API call is a downstream index update. If the
  API is unreachable (common in dry-run / status / offline development), the
  client returns ``False`` and the caller logs it, but the crawl proceeds.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Optional


DEFAULT_BASE_URL = os.environ.get("GLINTSTONE_API_BASE_URL", "http://127.0.0.1:8000")
# How long a single API write may take before we give up and let the crawl
# move on. Kept short — a slow index update must never stall the crawler.
_TIMEOUT_S = 10


@dataclass(frozen=True)
class ApiResult:
    ok: bool
    status_code: Optional[int]
    detail: Optional[str] = None


class ApiClient:
    """Minimal POST/GET client over curl for the ingestion layer."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")

    def record_image_path(
        self,
        *,
        p_number: str,
        image_type: str,
        local_path: str,
        source_url: str,
        size_bytes: Optional[int] = None,
    ) -> ApiResult:
        """Register a downloaded image's on-disk location with the API.

        Best-effort: returns an ``ApiResult`` describing the outcome and never
        raises. ``image_type`` is ``"photo"`` or ``"lineart"``.
        """
        payload = {
            "p_number": p_number,
            "image_type": image_type,
            "local_path": local_path,
            "source_url": source_url,
            "size_bytes": size_bytes,
        }
        return self._post("/internal/artifact-images", payload)

    # --- transport -------------------------------------------------------

    def _post(self, path: str, payload: dict) -> ApiResult:
        url = f"{self.base_url}{path}"
        sep = "\x1e"
        write_out = f"{sep}__META__{sep}%{{http_code}}"
        cmd = [
            "curl",
            "-s",
            "-S",
            "-X",
            "POST",
            "-H",
            "Content-Type: application/json",
            "--max-time",
            str(_TIMEOUT_S),
            "-d",
            json.dumps(payload),
            "-w",
            write_out,
            url,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, check=False)
        except FileNotFoundError:
            return ApiResult(ok=False, status_code=None, detail="curl not on PATH")
        if result.returncode != 0:
            return ApiResult(
                ok=False,
                status_code=None,
                detail=result.stderr.decode("utf-8", errors="replace").strip()
                or f"curl exited {result.returncode}",
            )
        stdout = result.stdout.decode("utf-8", errors="replace")
        marker = f"{sep}__META__{sep}"
        idx = stdout.rfind(marker)
        if idx < 0:
            return ApiResult(ok=False, status_code=None, detail="missing meta trailer")
        body = stdout[:idx]
        try:
            status_code = int(stdout[idx + len(marker) :].strip())
        except ValueError:
            return ApiResult(ok=False, status_code=None, detail="unparseable status")
        return ApiResult(
            ok=200 <= status_code < 300,
            status_code=status_code,
            detail=body[:200] or None,
        )
