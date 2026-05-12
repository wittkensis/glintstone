"""Rate-limited HTTP fetcher for CDLI.

Uses ``curl`` via subprocess because Python's ``urllib``/``requests``/``httpx``
have intermittent SSL issues on macOS against some CDLI endpoints (see
CLAUDE.md non-negotiable: "macOS SSL workaround").

Two rate-limit floors enforced via a single per-process lock:
1. ``min_interval_s`` — courtesy minimum between any two CDLI requests
   (default 5s; applies to both on-demand and background paths).
2. ``crawl_delay_s`` — the robots.txt Crawl-delay value (default 60s),
   enforced ONLY when caller passes ``respect_crawl_delay=True``
   (background backfill).

Both rules are advisory in the wild; we honor them because CDLI is a peer
academic institution we cite in the README.
"""

from __future__ import annotations

import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Optional

from core.config import get_settings


@dataclass(frozen=True)
class FetchResult:
    status_code: int
    body: bytes
    content_type: Optional[str]
    final_url: str


class FetchError(Exception):
    """Raised when curl exits non-zero or the response isn't usable."""


_lock = threading.Lock()
_last_request_at: float = 0.0


def _throttle(
    min_interval_s: float, crawl_delay_s: float, respect_crawl_delay: bool
) -> None:
    """Block until enough time has passed since the last CDLI request."""
    global _last_request_at
    required = crawl_delay_s if respect_crawl_delay else min_interval_s
    with _lock:
        elapsed = time.monotonic() - _last_request_at
        if elapsed < required:
            time.sleep(required - elapsed)
        _last_request_at = time.monotonic()


def fetch(
    url: str,
    *,
    respect_crawl_delay: bool,
    user_agent: Optional[str] = None,
    timeout_s: float = 30.0,
    accept: Optional[str] = None,
) -> FetchResult:
    """Fetch ``url`` honoring our rate-limit floor. Follows redirects (CDLI 302s).

    Returns FetchResult even on 4xx/5xx so the caller can log the outcome.
    Raises FetchError only on curl-level failures (network, timeout, no response).
    """
    settings = get_settings()
    ua = user_agent or settings.cdli_user_agent
    _throttle(
        min_interval_s=settings.cdli_min_request_interval_seconds,
        crawl_delay_s=settings.cdli_crawl_delay_seconds,
        respect_crawl_delay=respect_crawl_delay,
    )

    # -L follow redirects; -s silent; -S show error on failure; -A user-agent;
    # --max-time hard timeout; -w writes status code + final URL + content-type
    # to stdout AFTER the body, separated by null bytes for safe parsing.
    sep = "\x1e"  # ASCII record separator — unlikely in image/HTML bodies
    write_out = (
        f"{sep}__META__{sep}%{{http_code}}{sep}%{{url_effective}}{sep}%{{content_type}}"
    )
    cmd = [
        "curl",
        "-L",
        "-s",
        "-S",
        "-A",
        ua,
        "--max-time",
        str(int(timeout_s)),
        "-w",
        write_out,
        url,
    ]
    if accept:
        cmd += ["-H", f"Accept: {accept}"]

    try:
        result = subprocess.run(cmd, capture_output=True, check=False)
    except FileNotFoundError as e:
        raise FetchError(f"curl not on PATH: {e}") from e

    if result.returncode != 0:
        raise FetchError(
            f"curl exited {result.returncode} for {url}: "
            f"{result.stderr.decode('utf-8', errors='replace').strip()}"
        )

    stdout = result.stdout
    marker = f"{sep}__META__{sep}".encode()
    idx = stdout.rfind(marker)
    if idx < 0:
        raise FetchError(f"curl output missing metadata trailer for {url}")
    body = stdout[:idx]
    meta = stdout[idx + len(marker) :].decode("utf-8", errors="replace")
    parts = meta.split(sep)
    if len(parts) < 3:
        raise FetchError(f"unparseable curl meta for {url}: {meta!r}")
    status_code = int(parts[0])
    final_url = parts[1]
    content_type = parts[2] or None
    return FetchResult(
        status_code=status_code,
        body=body,
        content_type=content_type,
        final_url=final_url,
    )
