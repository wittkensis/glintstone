"""Backfill missing artifact images.

The main CDLI image crawler iterates ``artifacts`` and fetches images for any
P-number not yet represented in ``artifact_images``. That leaves a gap: if an
artifact had one image succeed and another fail (network blip, R2 hiccup,
parser miss), the crawler considers the artifact "done" because at least one
row exists, and the missing image is never retried.

This script closes that gap. It consults ``artifact_image_fetch_log`` — every
fetch attempt is logged with the source URL and outcome — to find image URLs
that failed and were never followed by a success. For each affected P-number
it re-fetches the artifact page, diffs the manifest against what's already in
``artifact_images``, and fetches only the missing entries.

Coordination with the main crawler is via the **shared lock file** at
``/tmp/glintstone-cdli-crawler.lock``. CDLI's robots.txt Crawl-delay is a
process-global ceiling, so the two scripts must never overlap.

Usage::

    python -m ops.scripts.backfill_missing_images --dry-run        # plan only
    python -m ops.scripts.backfill_missing_images --limit 5         # smoke
    python -m ops.scripts.backfill_missing_images --max-minutes 60  # cron run

Resumable via ``source-data/checkpoints/backfill_missing_images.json``.
Re-runs naturally pick up fewer candidates each time because successful
backfills land fresh ``outcome='success'`` rows in the log.
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.database import connect_one_shot  # noqa: E402
from core.storage import get_storage  # noqa: E402
from ingestion.images.fetcher import FetchError, fetch  # noqa: E402
from ingestion.images.parser import ImageRef, parse_artifact_page  # noqa: E402
from api.services.image_ondemand import (  # noqa: E402
    _fetch_and_store_one,
    _log_fetch_outcome,
)
from ops.scripts.cdli_image_crawler import (  # noqa: E402
    acquire_lock,
    release_lock,
)

CHECKPOINT_PATH = Path("source-data/checkpoints/backfill_missing_images.json")

ANNOTATION_RUN_SOURCE = "cdli-on-demand"
ANNOTATION_RUN_METHOD = "backfill_missing"


@dataclass
class BackfillCheckpoint:
    artifacts_examined: int = 0
    images_fetched: int = 0
    artifacts_complete_already: int = 0
    page_404: int = 0
    page_errors: int = 0
    image_errors: int = 0
    last_p_number: Optional[str] = None
    last_status_at: Optional[str] = None
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def load_checkpoint() -> BackfillCheckpoint:
    if CHECKPOINT_PATH.exists():
        with CHECKPOINT_PATH.open() as f:
            return BackfillCheckpoint(**json.load(f))
    return BackfillCheckpoint()


def save_checkpoint(cp: BackfillCheckpoint) -> None:
    cp.last_status_at = datetime.now(timezone.utc).isoformat()
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CHECKPOINT_PATH.with_suffix(".json.tmp")
    with tmp.open("w") as f:
        json.dump(asdict(cp), f, indent=2)
    tmp.replace(CHECKPOINT_PATH)


def find_candidates(conn, limit: Optional[int]) -> list[str]:
    """P-numbers with at least one failed IMAGE-BINARY fetch never followed by a success.

    Walks ``artifact_image_fetch_log`` for ``source_url`` values matching the
    CDLI image-binary pattern (``/dl/photo/`` or ``/dl/lineart/``). Page-level
    skip rows (where ``source_url`` is the artifact page itself) are
    intentionally excluded — those are negative-cache entries for the main
    crawler, not gaps for the backfill to retry.
    """
    sql = """
        WITH latest_per_url AS (
            SELECT DISTINCT ON (p_number, source_url)
                p_number, source_url, outcome
            FROM artifact_image_fetch_log
            WHERE source_url LIKE '%/dl/%'
            ORDER BY p_number, source_url, attempted_at DESC
        )
        SELECT DISTINCT p_number
        FROM latest_per_url
        WHERE outcome <> 'success'
        ORDER BY p_number
    """
    if limit is not None:
        sql += f" LIMIT {int(limit)}"
    with conn.cursor() as cur:
        cur.execute(sql)
        return [row["p_number"] for row in cur.fetchall()]


def existing_image_keys(conn, p_number: str) -> set[tuple[str, Optional[int]]]:
    """Return the (image_type, cdli_reader_id) tuples already present for this P-number."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT image_type, cdli_reader_id FROM artifact_images WHERE p_number = %s",
            (p_number,),
        )
        return {(r["image_type"], r["cdli_reader_id"]) for r in cur.fetchall()}


def ensure_backfill_run(conn) -> int:
    """SELECT-or-INSERT the annotation_run row that tags backfilled images.

    Separate from the main on-demand run so the curator can later identify which
    images were filled in by a gap-closing backfill pass.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id FROM annotation_runs
            WHERE source_type = 'import'
              AND source_name = %s
              AND method = %s
            ORDER BY id DESC LIMIT 1
            """,
            (ANNOTATION_RUN_SOURCE, ANNOTATION_RUN_METHOD),
        )
        row = cur.fetchone()
        if row:
            return row["id"]
        cur.execute(
            """
            INSERT INTO annotation_runs
                (source_type, source_name, method, notes, created_at)
            VALUES ('import', %s, %s, %s, now())
            RETURNING id
            """,
            (
                ANNOTATION_RUN_SOURCE,
                ANNOTATION_RUN_METHOD,
                "Gap-filling backfill for artifact_images rows missed by the main crawler.",
            ),
        )
        new_id = cur.fetchone()["id"]
    conn.commit()
    return new_id


def process_artifact(
    conn,
    storage,
    p_number: str,
    annotation_run_id: int,
    cp: BackfillCheckpoint,
) -> None:
    """Re-fetch the CDLI page for one P-number and fetch only the missing images.

    Updates the checkpoint counters in place; never raises — errors are logged
    to ``artifact_image_fetch_log`` and counted so cron output stays clean.
    """
    cp.artifacts_examined += 1
    cp.last_p_number = p_number

    try:
        page = fetch(f"https://cdli.earth/{p_number}", respect_crawl_delay=True)
    except FetchError as e:
        cp.page_errors += 1
        _log_fetch_outcome(
            conn,
            p_number=p_number,
            source_url=f"https://cdli.earth/{p_number}",
            outcome="other_error",
            http_status=None,
            error_message=f"page fetch failed: {e}",
            artifact_image_id=None,
        )
        return

    if page.status_code == 404:
        cp.page_404 += 1
        return
    if page.status_code != 200:
        cp.page_errors += 1
        _log_fetch_outcome(
            conn,
            p_number=p_number,
            source_url=f"https://cdli.earth/{p_number}",
            outcome="http_5xx" if page.status_code >= 500 else "other_error",
            http_status=page.status_code,
            error_message=f"HTTP {page.status_code} for artifact page",
            artifact_image_id=None,
        )
        return

    manifest = parse_artifact_page(
        page.body.decode("utf-8", errors="replace"), p_number
    )
    present = existing_image_keys(conn, p_number)

    missing: list[tuple[int, ImageRef]] = [
        (i, ref)
        for i, ref in enumerate(manifest.images)
        if (ref.image_type, ref.cdli_reader_id) not in present
    ]
    if not missing:
        cp.artifacts_complete_already += 1
        return

    for display_order, ref in missing:
        try:
            inserted = _fetch_and_store_one(
                conn=conn,
                storage=storage,
                p_number=p_number,
                ref=ref,
                display_order=display_order,
                annotation_run_id=annotation_run_id,
                respect_crawl_delay=True,
            )
            if inserted:
                cp.images_fetched += 1
            else:
                cp.image_errors += 1
        except Exception as e:
            cp.image_errors += 1
            _log_fetch_outcome(
                conn,
                p_number=p_number,
                source_url=ref.full_url,
                outcome="other_error",
                http_status=None,
                error_message=str(e),
                artifact_image_id=None,
            )


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process at most N candidate P-numbers (default: all).",
    )
    ap.add_argument(
        "--max-minutes",
        type=int,
        default=None,
        help="Soft wall-time budget. Finishes the current artifact then exits.",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan only; report candidate count and exit without fetching.",
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
    deadline: Optional[float] = (
        time.monotonic() + args.max_minutes * 60 if args.max_minutes else None
    )

    try:
        candidates = find_candidates(conn, args.limit)
        print(
            f"Candidate artifacts (failures with no later success): {len(candidates):,}"
        )
        if not candidates:
            return 0

        if args.dry_run:
            print(f"  first 10: {', '.join(candidates[:10])}")
            return 0

        annotation_run_id = ensure_backfill_run(conn)
        storage = get_storage()

        for i, p_number in enumerate(candidates, start=1):
            if stop_requested["value"]:
                print(f"Stopped at {p_number} ({i - 1}/{len(candidates)} processed).")
                break
            if deadline is not None and time.monotonic() >= deadline:
                print(
                    f"Hit --max-minutes budget at {p_number} "
                    f"({i - 1}/{len(candidates)} processed)."
                )
                break

            process_artifact(conn, storage, p_number, annotation_run_id, cp)

            if i % 5 == 0:
                save_checkpoint(cp)
                print(
                    f"  [{i}/{len(candidates)}] "
                    f"images_fetched={cp.images_fetched} "
                    f"complete_already={cp.artifacts_complete_already} "
                    f"page_404={cp.page_404} "
                    f"page_errors={cp.page_errors} "
                    f"image_errors={cp.image_errors}",
                    flush=True,
                )

        save_checkpoint(cp)
        print()
        print(
            f"Done. examined={cp.artifacts_examined} "
            f"images_fetched={cp.images_fetched} "
            f"complete_already={cp.artifacts_complete_already} "
            f"page_404={cp.page_404} "
            f"page_errors={cp.page_errors} "
            f"image_errors={cp.image_errors}"
        )
        return 0
    finally:
        save_checkpoint(cp)
        conn.close()
        if not args.dry_run:
            release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
