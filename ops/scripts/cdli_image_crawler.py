"""Background CDLI image crawler.

Iterates the ``artifacts`` table and, for each P-number not yet in
``artifact_images``, fetches the CDLI artifact page, parses the image manifest,
downloads originals, generates WebP thumbnails, and stores everything in R2 +
the database.

Strict 60-second rate limit per request (CDLI's robots.txt Crawl-delay = 60).
With ~350k artifacts and an estimated 40% imagery hit rate, expect this to
run for **months**, not hours. Designed to be left running as a long-lived
background process with resumable checkpointing.

Coordination with other crawlers:
- Uses a file-based lock at /tmp/glintstone-cdli-crawler.lock so two crawler
  instances can't run simultaneously.
- Does NOT coordinate with ``backfill_image_attribution.py`` — do not run
  both at the same time, or you'll exceed CDLI's rate limit.

Usage:
    python -m ops.scripts.cdli_image_crawler --dry-run               # plan
    python -m ops.scripts.cdli_image_crawler --limit 100             # smoke
    python -m ops.scripts.cdli_image_crawler                         # forever
    python -m ops.scripts.cdli_image_crawler --order p_number_desc   # newest P-numbers first

Resumable: skips P-numbers already represented in artifact_images. Re-running
after Ctrl-C picks up where it left off.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.database import connect_one_shot  # noqa: E402
from api.services.image_ondemand import ensure_images_for_artifact  # noqa: E402

CHECKPOINT_PATH = Path("source-data/checkpoints/cdli_image_crawler.json")
LOCK_PATH = Path("/tmp/glintstone-cdli-crawler.lock")


@dataclass
class CrawlerCheckpoint:
    fetched: int = 0
    cached: int = 0
    not_found: int = 0
    errors: int = 0
    last_p_number: Optional[str] = None
    last_status_at: Optional[str] = None
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def load_checkpoint() -> CrawlerCheckpoint:
    if CHECKPOINT_PATH.exists():
        with CHECKPOINT_PATH.open() as f:
            return CrawlerCheckpoint(**json.load(f))
    return CrawlerCheckpoint()


def save_checkpoint(cp: CrawlerCheckpoint) -> None:
    cp.last_status_at = datetime.now(timezone.utc).isoformat()
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CHECKPOINT_PATH.with_suffix(".json.tmp")
    with tmp.open("w") as f:
        json.dump(asdict(cp), f, indent=2)
    tmp.replace(CHECKPOINT_PATH)


def acquire_lock() -> None:
    """File-based lock so only one crawler runs at a time.

    Writes our PID into the lock file. If the file exists and the PID inside
    is still alive, refuse to start. Stale PIDs (process gone) are reclaimed.
    """
    if LOCK_PATH.exists():
        try:
            existing_pid = int(LOCK_PATH.read_text().strip())
        except (ValueError, OSError):
            existing_pid = None
        if existing_pid:
            try:
                os.kill(existing_pid, 0)  # signal 0 = liveness check
                raise SystemExit(
                    f"Another crawler is running (PID {existing_pid}). "
                    f"Lock at {LOCK_PATH}."
                )
            except ProcessLookupError:
                # Stale lock from a dead PID — reclaim.
                LOCK_PATH.unlink(missing_ok=True)
    LOCK_PATH.write_text(str(os.getpid()))


def release_lock() -> None:
    if LOCK_PATH.exists():
        try:
            if int(LOCK_PATH.read_text().strip()) == os.getpid():
                LOCK_PATH.unlink()
        except (ValueError, OSError):
            pass


def candidates(conn, order: str, limit: Optional[int]) -> list[str]:
    """P-numbers in ``artifacts`` not yet in ``artifact_images`` and not in
    the page-level skip cache.

    Excludes:
    - artifacts that already have one or more rows in ``artifact_images``
      (the main resume signal)
    - artifacts with a recent page-level skip recorded in
      ``artifact_image_fetch_log`` (404 or no-images). The skip cache TTL
      matches ``api.services.image_ondemand.PAGE_SKIP_TTL_DAYS`` (90 days)
      so previously-removed pages get re-checked eventually.
    """
    from api.services.image_ondemand import (  # noqa: E402
        PAGE_SKIP_OUTCOMES,
        PAGE_SKIP_TTL_DAYS,
    )

    order_clause = "a.p_number DESC" if order == "p_number_desc" else "a.p_number ASC"
    sql = f"""
        SELECT a.p_number
        FROM artifacts a
        WHERE NOT EXISTS (
            SELECT 1 FROM artifact_images ai WHERE ai.p_number = a.p_number
        )
        AND NOT EXISTS (
            SELECT 1 FROM artifact_image_fetch_log fl
            WHERE fl.p_number = a.p_number
              AND fl.outcome = ANY(%s)
              AND fl.attempted_at > now() - interval '{PAGE_SKIP_TTL_DAYS} days'
        )
        ORDER BY {order_clause}
    """
    if limit is not None:
        sql += f" LIMIT {int(limit)}"
    with conn.cursor() as cur:
        cur.execute(sql, (list(PAGE_SKIP_OUTCOMES),))
        return [row["p_number"] for row in cur.fetchall()]


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process at most N artifacts (useful for smoke tests).",
    )
    ap.add_argument(
        "--order",
        choices=("p_number_asc", "p_number_desc"),
        default="p_number_asc",
        help="Crawl order (asc = oldest CDLI entries first).",
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="Plan only; no fetches, no writes."
    )
    args = ap.parse_args(argv)

    if not args.dry_run:
        acquire_lock()

    stop_requested = {"value": False}

    def _signal(signum, _frame):
        stop_requested["value"] = True
        print(f"\n[signal {signum}] finishing current artifact, then stopping...")

    signal.signal(signal.SIGINT, _signal)
    signal.signal(signal.SIGTERM, _signal)

    conn = connect_one_shot()
    cp = load_checkpoint()
    try:
        targets = candidates(conn, args.order, args.limit)
        print(f"Pending artifacts (no rows in artifact_images): {len(targets):,}")
        if not targets:
            return 0

        if args.dry_run:
            preview = ", ".join(targets[:10])
            print(f"  first 10: {preview}")
            est_days = len(targets) * 60 / 86400
            print(f"Estimated runtime at 60s/req: ~{est_days:.0f} days")
            return 0

        for i, p_number in enumerate(targets, start=1):
            if stop_requested["value"]:
                print(f"Stopped at {p_number} ({i - 1}/{len(targets)} processed).")
                break

            result = ensure_images_for_artifact(
                conn, p_number, respect_crawl_delay=True
            )
            cp.last_p_number = p_number
            if result.status == "cached":
                cp.cached += 1
            elif result.status == "fetched":
                cp.fetched += 1
                print(
                    f"[{i}/{len(targets)}] {p_number}: fetched {result.image_count} image(s)"
                )
            elif result.status == "not_found_at_cdli":
                cp.not_found += 1
            else:
                cp.errors += 1
                print(
                    f"[{i}/{len(targets)}] {p_number}: {result.status} — {result.detail}"
                )

            # Checkpoint every 10 artifacts to keep disk writes bounded.
            if i % 10 == 0:
                save_checkpoint(cp)
                print(
                    f"  ... [{i}/{len(targets)}] "
                    f"fetched={cp.fetched} cached={cp.cached} "
                    f"not_found={cp.not_found} errors={cp.errors}",
                    flush=True,
                )

        save_checkpoint(cp)
        print()
        print(
            f"Done. fetched={cp.fetched} cached={cp.cached} "
            f"not_found={cp.not_found} errors={cp.errors}"
        )
        return 0
    finally:
        save_checkpoint(cp)
        conn.close()
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
