"""CDLI tablet-image backfill — resumable, rate-limited crawler.

CDLI hosts artifact imagery on GWDG (Gesellschaft fur wissenschaftliche
Datenverarbeitung Gottingen) infrastructure. Each artifact P-number can have a
*photo* and/or a *lineart* (hand-drawn copy) variant, at a deterministic URL:

    https://cdli.mpiwg-berlin.mpg.de/dl/lineart/{P_NUMBER}.jpg
    https://cdli.mpiwg-berlin.mpg.de/dl/photo/{P_NUMBER}.jpg

This connector walks every known P-number, downloads both variants where they
exist, saves them to local disk, and registers each file's path with the API.

Why a standalone job queue (not just the framework's import_runs)?
------------------------------------------------------------------
This is a *long, interruptible* crawl: hundreds of thousands of P-numbers at a
polite 3-seconds-per-request floor is days of wall time, and GWDG previously
*rate-limited / blocked* the crawler entirely (backlog #524). We therefore keep
an external, human-readable queue on disk so a restart picks up exactly where
it stopped without re-hitting already-done artifacts:

    ~/.claude/state/cdli-image-queue.json
    {
      "last_run": "2026-06-26T...",
      "pending": ["P000001", ...],   # not yet attempted
      "done":    ["P000003", ...],   # at least one variant fetched (or both 404)
      "failed":  [{"p_number": "P000004", "reason": "404", "attempts": 1}, ...]
    }

A health line is appended to ~/.claude/logs/cdli-image-scraper.log after every
100 P-numbers so a watcher (or Eric, from his phone) can see throughput.

The connector is auto-discovered by ``ingestion.registry`` via its ``id``
("cdli-images"), so ``python -m ingestion.cli run cdli-images`` works, and it
also runs standalone as a CLI for the operational flags ``--resume`` /
``--dry-run`` / ``--status``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Optional

# Allow `python3 ingestion/connectors/cdli_images.py` to run standalone: when
# invoked as a script, only this file's directory is on sys.path, so the repo
# root (which holds the `ingestion` package) must be added explicitly. This is
# a no-op when imported as a module by the framework.
if __package__ in (None, ""):
    _REPO_ROOT = Path(__file__).resolve().parents[2]
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))

from ingestion.base import LoadStats, RunContext, SourceConnector

# --- constants ----------------------------------------------------------

GWDG_BASE = "https://cdli.mpiwg-berlin.mpg.de/dl"
IMAGE_TYPES = ("lineart", "photo")

# Polite crawl floor: one request every 3 seconds.
RATE_LIMIT_SECONDS = 3.0
# Exponential backoff schedule when GWDG signals overload (429 / 503).
BACKOFF_SCHEDULE_SECONDS = (30, 60, 120)
# Statuses that mean "back off and retry the SAME request", not "give up".
RETRYABLE_STATUSES = frozenset({429, 503})

# Where state lives. Overridable via env for tests / alternate hosts.
QUEUE_PATH = Path(
    os.environ.get(
        "CDLI_IMAGE_QUEUE_PATH",
        str(Path.home() / ".claude" / "state" / "cdli-image-queue.json"),
    )
)
LOG_PATH = Path(
    os.environ.get(
        "CDLI_IMAGE_LOG_PATH",
        str(Path.home() / ".claude" / "logs" / "cdli-image-scraper.log"),
    )
)
# VPS storage root. Photos and linearts go in sibling subdirs.
STORAGE_ROOT = Path(os.environ.get("CDLI_IMAGE_STORAGE_ROOT", "/data/cdli-images"))

# Emit a health line after this many P-numbers processed.
HEALTH_EVERY = 100


# --- job queue ----------------------------------------------------------


@dataclass
class FailedItem:
    p_number: str
    reason: str
    attempts: int

    def to_dict(self) -> dict:
        return {"p_number": self.p_number, "reason": self.reason, "attempts": self.attempts}

    @classmethod
    def from_dict(cls, d: dict) -> "FailedItem":
        return cls(
            p_number=d["p_number"],
            reason=d.get("reason", "unknown"),
            attempts=int(d.get("attempts", 1)),
        )


class JobQueue:
    """Resumable, crash-safe-ish job queue persisted as JSON.

    ``pending`` / ``done`` are ordered lists kept de-duplicated via membership
    sets. ``failed`` keeps the per-P-number reason + attempt count so a later
    pass can decide whether a P-number is worth retrying.

    Persistence uses an atomic write (temp file + ``os.replace``) so a crash
    mid-write can't truncate the queue. We do NOT fsync per save — at one save
    per 100 items the worst case on a hard crash is re-doing <100 already-done
    artifacts, which is harmless (downloads are idempotent).
    """

    def __init__(self, path: Path = QUEUE_PATH) -> None:
        self.path = path
        self.last_run: Optional[str] = None
        self.pending: list[str] = []
        self.done: list[str] = []
        self.failed: list[FailedItem] = []
        self._done_set: set[str] = set()
        self._pending_set: set[str] = set()
        if path.exists():
            self._load()

    def _load(self) -> None:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.last_run = data.get("last_run")
        self.pending = list(data.get("pending", []))
        self.done = list(data.get("done", []))
        self.failed = [FailedItem.from_dict(f) for f in data.get("failed", [])]
        self._pending_set = set(self.pending)
        self._done_set = set(self.done)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "last_run": self.last_run or _utc_iso(),
            "pending": self.pending,
            "done": self.done,
            "failed": [f.to_dict() for f in self.failed],
        }
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    def enqueue(self, p_numbers: Iterable[str]) -> int:
        """Add P-numbers to ``pending`` that aren't already pending or done.

        Returns the count actually added. Idempotent: re-seeding from the same
        source on every run is safe and cheap.
        """
        added = 0
        for p in p_numbers:
            p = p.strip()
            if not p or p in self._pending_set or p in self._done_set:
                continue
            self.pending.append(p)
            self._pending_set.add(p)
            added += 1
        return added

    def next_batch(self, limit: Optional[int] = None) -> list[str]:
        """Return the head of the pending list without removing it."""
        if limit is None:
            return list(self.pending)
        return self.pending[:limit]

    def mark_done(self, p_number: str) -> None:
        self._remove_pending(p_number)
        # Drop any prior failure record now that it has succeeded.
        self.failed = [f for f in self.failed if f.p_number != p_number]
        if p_number not in self._done_set:
            self.done.append(p_number)
            self._done_set.add(p_number)

    def mark_failed(self, p_number: str, reason: str) -> None:
        self._remove_pending(p_number)
        for f in self.failed:
            if f.p_number == p_number:
                f.attempts += 1
                f.reason = reason
                return
        self.failed.append(FailedItem(p_number=p_number, reason=reason, attempts=1))

    def _remove_pending(self, p_number: str) -> None:
        if p_number in self._pending_set:
            self._pending_set.discard(p_number)
            # Lazy removal: rebuild the list only when present (rare hot loop).
            self.pending = [p for p in self.pending if p != p_number]

    def stats(self) -> dict:
        return {
            "last_run": self.last_run,
            "pending": len(self.pending),
            "done": len(self.done),
            "failed": len(self.failed),
        }


# --- download core ------------------------------------------------------


@dataclass(frozen=True)
class FetchOutcome:
    saved: list[str]  # local paths written this call
    missing: list[str]  # image_types that returned 404 (legitimately absent)
    error: Optional[str]  # set if the whole P-number should be marked failed


def image_url(p_number: str, image_type: str) -> str:
    return f"{GWDG_BASE}/{image_type}/{p_number}.jpg"


def local_path_for(p_number: str, image_type: str, root: Path = STORAGE_ROOT) -> Path:
    return root / image_type / f"{p_number}.jpg"


class CdliImageScraper:
    """Owns the crawl loop: rate limiting, backoff, disk writes, API records.

    The HTTP layer is injected (``fetch_fn``) so this stays testable without a
    network. By default it uses ``ingestion.images.fetcher.fetch``, which goes
    through ``curl`` (the documented macOS SSL workaround) and enforces a
    process-wide courtesy floor of its own.
    """

    def __init__(
        self,
        queue: JobQueue,
        *,
        storage_root: Path = STORAGE_ROOT,
        rate_limit_seconds: float = RATE_LIMIT_SECONDS,
        fetch_fn=None,
        api_client=None,
        sleep_fn=time.sleep,
        log_fn=None,
    ) -> None:
        self.queue = queue
        self.storage_root = storage_root
        self.rate_limit_seconds = rate_limit_seconds
        self._fetch_fn = fetch_fn
        self._api_client = api_client
        self._sleep = sleep_fn
        self._log = log_fn or (lambda msg: print(msg))
        self._processed_since_start = 0
        self._run_started = time.monotonic()

    # -- lazy deps so --status / --dry-run don't import network/PIL stacks --

    def _fetch(self):
        if self._fetch_fn is None:
            from ingestion.images.fetcher import fetch as _fetch

            self._fetch_fn = _fetch
        return self._fetch_fn

    def _api(self):
        if self._api_client is None:
            from ingestion.api_client import ApiClient

            self._api_client = ApiClient()
        return self._api_client

    # -- one image variant, with backoff on overload --------------------

    def _fetch_one(self, p_number: str, image_type: str) -> tuple[Optional[bytes], Optional[str]]:
        """Fetch a single variant. Returns (body, error).

        On 429/503 it backs off through BACKOFF_SCHEDULE_SECONDS, retrying the
        same request. Returns (None, None) for a clean 404 (image just doesn't
        exist — not an error). Returns (None, "<reason>") for a real failure.
        """
        url = image_url(p_number, image_type)
        fetch = self._fetch()
        attempt = 0
        while True:
            self._sleep(self.rate_limit_seconds)
            try:
                res = fetch(url, respect_crawl_delay=False)
            except Exception as e:  # noqa: BLE001 — surface as a failure reason
                return None, f"fetch_error: {e}"

            if res.status_code == 404:
                return None, None
            if 200 <= res.status_code < 300:
                if not res.body:
                    return None, "empty_body"
                return res.body, None
            if res.status_code in RETRYABLE_STATUSES:
                if attempt >= len(BACKOFF_SCHEDULE_SECONDS):
                    return None, f"http_{res.status_code}_exhausted"
                wait = BACKOFF_SCHEDULE_SECONDS[attempt]
                self._log(
                    f"  [backoff] {p_number}/{image_type} got {res.status_code}; "
                    f"sleeping {wait}s (attempt {attempt + 1})"
                )
                self._sleep(wait)
                attempt += 1
                continue
            return None, f"http_{res.status_code}"

    def process(self, p_number: str) -> FetchOutcome:
        """Fetch both variants for one P-number and persist what exists."""
        saved: list[str] = []
        missing: list[str] = []
        for image_type in IMAGE_TYPES:
            body, error = self._fetch_one(p_number, image_type)
            if error is not None:
                # A hard error on one variant fails the whole P-number so it's
                # retried later; partial successes already on disk are kept.
                return FetchOutcome(saved=saved, missing=missing, error=error)
            if body is None:
                missing.append(image_type)
                continue
            dest = local_path_for(p_number, image_type, self.storage_root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(body)
            saved.append(str(dest))
            self._record(p_number, image_type, dest, len(body))
        return FetchOutcome(saved=saved, missing=missing, error=None)

    def _record(self, p_number: str, image_type: str, dest: Path, size: int) -> None:
        try:
            res = self._api().record_image_path(
                p_number=p_number,
                image_type=image_type,
                local_path=str(dest),
                source_url=image_url(p_number, image_type),
                size_bytes=size,
            )
            if not res.ok:
                self._log(
                    f"  [warn] API did not record {p_number}/{image_type} "
                    f"(status={res.status_code}); file is on disk, index update deferred"
                )
        except Exception as e:  # noqa: BLE001 — index update is best-effort
            self._log(f"  [warn] API record raised for {p_number}/{image_type}: {e}")

    # -- the run loop ----------------------------------------------------

    def run(self, limit: Optional[int] = None) -> dict:
        """Drain the pending queue (up to ``limit`` P-numbers). Returns stats."""
        batch = self.queue.next_batch(limit)
        for p_number in batch:
            outcome = self.process(p_number)
            if outcome.error is not None:
                self.queue.mark_failed(p_number, outcome.error)
                self._log(f"  [fail] {p_number}: {outcome.error}")
            else:
                self.queue.mark_done(p_number)
                if outcome.saved:
                    self._log(
                        f"  [done] {p_number}: saved {len(outcome.saved)} "
                        f"({', '.join(Path(s).parent.name for s in outcome.saved)})"
                    )
                else:
                    self._log(f"  [done] {p_number}: no images upstream (404)")
            self._processed_since_start += 1
            if self._processed_since_start % HEALTH_EVERY == 0:
                self.queue.last_run = _utc_iso()
                self.queue.save()
                self._write_health_line()
        # Final save so the queue reflects a partial-batch tail.
        self.queue.last_run = _utc_iso()
        self.queue.save()
        return self.queue.stats()

    def _write_health_line(self) -> None:
        elapsed_min = max((time.monotonic() - self._run_started) / 60.0, 1e-9)
        rate = self._processed_since_start / elapsed_min
        s = self.queue.stats()
        line = (
            f"[{_utc_iso()}] done={s['done']} failed={s['failed']} "
            f"pending={s['pending']} rate={rate:.1f} img/min\n"
        )
        try:
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line)
        except OSError as e:
            self._log(f"  [warn] could not write health line: {e}")
        self._log(line.rstrip())


# --- P-number seeding ---------------------------------------------------


def seed_p_numbers_from_db(ctx: RunContext, limit: Optional[int] = None) -> Iterator[str]:
    """Yield P-numbers from the staged CDLI catalog (artifacts we know exist).

    Ordered ascending so the crawl is deterministic and resumable. Reads from
    ``staging_cdli_catalog`` (populated by the cdli-catalog connector); falls
    back to ``artifacts`` if staging is empty.
    """
    sql = "SELECT p_number FROM staging_cdli_catalog ORDER BY p_number"
    if limit:
        sql += f" LIMIT {int(limit)}"
    rows = ctx.db.execute(sql).fetchall()
    for row in rows:
        yield row["p_number"] if isinstance(row, dict) else row[0]


# --- connector (framework entry point) ----------------------------------


class CdliImagesConnector(SourceConnector):
    """Auto-discovered framework connector wrapping the scraper.

    ``python -m ingestion.cli run cdli-images`` drains the queue, seeding it
    from the staged catalog first. Long crawls are better driven via the
    standalone ``--resume`` CLI (so they can run detached), but the framework
    entry point exists for orchestration and dependency ordering.
    """

    id = "cdli-images"
    display_name = "CDLI Tablet Images (GWDG)"
    description = (
        "Backfills photo + lineart imagery for CDLI artifacts from GWDG hosting, "
        "resumably and rate-limited (1 req / 3s, exponential backoff on overload)."
    )
    kind = "derived"
    runs_after = ["cdli-catalog"]
    license = "CC-BY-NC-3.0"
    license_url = "https://creativecommons.org/licenses/by-nc/3.0/"
    upstream_url = "https://cdli.mpiwg-berlin.mpg.de/"
    citation = (
        "Cuneiform Digital Library Initiative (CDLI), "
        "https://cdli.mpiwg-berlin.mpg.de/ — artifact imagery via GWDG."
    )
    contact_email = "cdli@cdli.mpiwg-berlin.mpg.de"

    def __init__(self, batch_limit: Optional[int] = None) -> None:
        self.batch_limit = batch_limit

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        queue = JobQueue()
        added = queue.enqueue(seed_p_numbers_from_db(ctx))
        queue.save()
        ctx.info("cdli_images.seeded", added=added, **queue.stats())
        yield {"queue": queue}

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        stats = LoadStats()
        for row in rows:
            queue: JobQueue = row["queue"]
            scraper = CdliImageScraper(queue, log_fn=lambda m: ctx.info("cdli_images.progress", line=m))
            result = scraper.run(limit=self.batch_limit)
            ctx.info("cdli_images.run_complete", **result)
            stats.inserted += result["done"]
            stats.dead_lettered += result["failed"]
        return stats


# --- helpers ------------------------------------------------------------


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- standalone CLI -----------------------------------------------------


def _print_status(queue: JobQueue) -> None:
    s = queue.stats()
    print("CDLI image scraper — queue status")
    print(f"  queue file : {queue.path}")
    print(f"  last run   : {s['last_run'] or '(never)'}")
    print(f"  pending    : {s['pending']}")
    print(f"  done       : {s['done']}")
    print(f"  failed     : {s['failed']}")


def _dry_run(queue: JobQueue, n: int = 3) -> None:
    batch = queue.next_batch(n)
    print(f"Dry run — would fetch the first {len(batch)} pending P-number(s):")
    if not batch:
        print("  (queue empty — seed it by running the connector against the catalog)")
        return
    for p in batch:
        for image_type in IMAGE_TYPES:
            print(f"  GET {image_url(p, image_type)}")
            print(f"      -> {local_path_for(p, image_type)}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="CDLI image scraper — resumable, rate-limited GWDG crawler."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--resume", action="store_true", help="continue draining the queue")
    group.add_argument("--dry-run", action="store_true", help="show the first 3 P-numbers that would be fetched")
    group.add_argument("--status", action="store_true", help="print queue stats and exit")
    parser.add_argument("--limit", type=int, default=None, help="max P-numbers to process this run")
    parser.add_argument(
        "--seed-file",
        type=str,
        default=None,
        help="newline-delimited P-numbers to enqueue before resuming",
    )
    args = parser.parse_args(argv)

    queue = JobQueue()

    if args.seed_file:
        path = Path(args.seed_file)
        if not path.exists():
            print(f"seed file not found: {path}", file=sys.stderr)
            return 2
        added = queue.enqueue(path.read_text(encoding="utf-8").splitlines())
        queue.save()
        print(f"Seeded {added} new P-number(s) from {path}")

    if args.status or not (args.resume or args.dry_run):
        _print_status(queue)
        return 0
    if args.dry_run:
        _dry_run(queue)
        return 0
    if args.resume:
        scraper = CdliImageScraper(queue)
        result = scraper.run(limit=args.limit)
        print(f"Run complete: done={result['done']} failed={result['failed']} pending={result['pending']}")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
