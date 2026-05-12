"""HTML-only attribution backfill for artifact_images rows.

For rows where ``attribution_raw IS NULL`` (the 102 images uploaded by
``upload_local_images.py`` on 2026-05-12), fetch the corresponding CDLI
artifact page, parse the per-image attribution + cdli_reader_id, and update
the row. Does NOT fetch image binaries — they're already in R2.

Rate-limited to CDLI's robots.txt Crawl-delay (60s by default). One HTTP
request per artifact (not per image) since the artifact page lists all
of an artifact's images in one document.

Usage:
    python -m ops.scripts.backfill_image_attribution                # full run
    python -m ops.scripts.backfill_image_attribution --limit 5      # smoke
    python -m ops.scripts.backfill_image_attribution --dry-run      # report only

Resumable via checkpoint at source-data/checkpoints/backfill_attribution.json.
Re-running skips artifacts already attributed.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.database import connect_one_shot  # noqa: E402
from ingestion.images.fetcher import FetchError, fetch  # noqa: E402
from ingestion.images.parser import (  # noqa: E402
    build_credit_line,
    derive_copyright_holder,
    parse_artifact_page,
)

CHECKPOINT_PATH = Path("source-data/checkpoints/backfill_attribution.json")


@dataclass
class CheckpointState:
    attributed: list[str]
    no_match: list[str]
    failed: list[dict]
    started_at: str
    last_updated_at: str


def load_checkpoint() -> CheckpointState:
    if CHECKPOINT_PATH.exists():
        with CHECKPOINT_PATH.open() as f:
            return CheckpointState(**json.load(f))
    now = datetime.now(timezone.utc).isoformat()
    return CheckpointState(
        attributed=[], no_match=[], failed=[], started_at=now, last_updated_at=now
    )


def save_checkpoint(state: CheckpointState) -> None:
    state.last_updated_at = datetime.now(timezone.utc).isoformat()
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CHECKPOINT_PATH.with_suffix(".json.tmp")
    with tmp.open("w") as f:
        json.dump(asdict(state), f, indent=2)
    tmp.replace(CHECKPOINT_PATH)


def find_pending(conn, limit: Optional[int]) -> list[dict]:
    """artifact_images rows that need attribution.

    Groups by (p_number, image_type) so we make one HTML fetch per artifact
    even if the artifact has multiple images.
    """
    sql = """
        SELECT DISTINCT p_number
        FROM artifact_images
        WHERE attribution_raw IS NULL
        ORDER BY p_number
    """
    if limit is not None:
        sql += f" LIMIT {int(limit)}"
    with conn.cursor() as cur:
        cur.execute(sql)
        return [row["p_number"] for row in cur.fetchall()]


def update_row(
    conn,
    p_number: str,
    image_type: str,
    cdli_reader_id: Optional[int],
    attribution_raw: str,
    copyright_holder: Optional[str],
    credit_line: Optional[str],
) -> int:
    """Update the matching artifact_images row(s).

    Returns the number of rows updated. We match on (p_number, image_type)
    plus an OR for the NULL cdli_reader_id case — backfill is the first
    place where cdli_reader_id gets populated, so a row whose image_type
    matches and whose cdli_reader_id is still NULL is fair game.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE artifact_images
            SET attribution_raw = %(attribution_raw)s,
                copyright_holder = %(copyright_holder)s,
                credit_line = %(credit_line)s,
                cdli_reader_id = COALESCE(cdli_reader_id, %(cdli_reader_id)s)
            WHERE p_number = %(p_number)s
              AND image_type = %(image_type)s
              AND attribution_raw IS NULL
            """,
            {
                "p_number": p_number,
                "image_type": image_type,
                "cdli_reader_id": cdli_reader_id,
                "attribution_raw": attribution_raw,
                "copyright_holder": copyright_holder,
                "credit_line": credit_line,
            },
        )
        n = cur.rowcount
    conn.commit()
    return n


def attribute_one(conn, p_number: str) -> tuple[int, str]:
    """Fetch the artifact page, parse, update rows.

    Returns (updated_row_count, status_label).
    """
    url = f"https://cdli.earth/{p_number}"
    try:
        result = fetch(url, respect_crawl_delay=True)
    except FetchError as e:
        return 0, f"fetch_error:{e}"
    if result.status_code != 200:
        return 0, f"http_{result.status_code}"

    html = result.body.decode("utf-8", errors="replace")
    manifest = parse_artifact_page(html, p_number)
    if not manifest.images:
        return 0, "no_images_parsed"

    total_updated = 0
    for img in manifest.images:
        if not img.attribution_raw:
            continue
        n = update_row(
            conn,
            p_number=p_number,
            image_type=img.image_type,
            cdli_reader_id=img.cdli_reader_id,
            attribution_raw=img.attribution_raw,
            copyright_holder=derive_copyright_holder(img.attribution_raw),
            credit_line=build_credit_line(img.attribution_raw),
        )
        total_updated += n
    return total_updated, "ok" if total_updated else "no_match"


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--limit", type=int, default=None, help="Process at most N artifacts."
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="Show plan; no fetches, no writes."
    )
    args = ap.parse_args(argv)

    conn = connect_one_shot()
    try:
        pending = find_pending(conn, args.limit)
        print(f"Pending artifacts (attribution_raw IS NULL): {len(pending)}")
        if not pending:
            return 0

        if args.dry_run:
            for p in pending[:20]:
                print(f"  [dry-run] would fetch https://cdli.earth/{p}")
            if len(pending) > 20:
                print(f"  ... and {len(pending) - 20} more")
            est_minutes = len(pending) * 60 / 60
            print(f"Estimated runtime at 60s/req: ~{est_minutes:.0f} minutes")
            return 0

        state = load_checkpoint()
        try:
            for i, p_number in enumerate(pending, start=1):
                print(f"[{i}/{len(pending)}] {p_number} ...", flush=True)
                updated, status = attribute_one(conn, p_number)
                if status == "ok":
                    state.attributed.append(p_number)
                    print(f"    OK ({updated} rows updated)")
                elif status == "no_match":
                    state.no_match.append(p_number)
                    print("    no matching attribution parsed")
                else:
                    state.failed.append({"p_number": p_number, "status": status})
                    print(f"    {status}")
                save_checkpoint(state)
        finally:
            save_checkpoint(state)

        print()
        print(
            f"Done. attributed={len(state.attributed)} "
            f"no_match={len(state.no_match)} failed={len(state.failed)}"
        )
        if state.failed:
            print("Failures (first 10):")
            for f in state.failed[:10]:
                print(f"  - {f['p_number']}: {f['status']}")
        return 0 if not state.failed else 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
