"""One-time bulk upload of locally-downloaded CDLI tablet images to R2.

Walks the configured local-image directories (default: the repo's
``source-data/sources/CDLI/images/`` plus the iCloud archive copies),
dedupes by P-number, computes sha256, uploads original + generated WebP
thumbnail to R2, inserts an ``artifact_images`` row with
``attribution_raw IS NULL`` (marked for later HTML-only attribution backfill),
and deletes the local file ONLY after both uploads and the DB insert are
confirmed.

Usage:
    python -m ops.scripts.upload_local_images --dry-run
    python -m ops.scripts.upload_local_images
    python -m ops.scripts.upload_local_images --delete-after-upload

The script logs to stdout and to source-data/checkpoints/upload_local_images.json
so it's resumable. Re-running skips P-numbers already in artifact_images.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Make repo root importable when invoked as a script.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.database import connect_one_shot  # noqa: E402
from core.storage import artifact_image_key, get_storage  # noqa: E402
from ingestion.images.thumbnailer import generate_thumbnail, probe_dimensions  # noqa: E402

CHECKPOINT_PATH = Path("source-data/checkpoints/upload_local_images.json")

DEFAULT_SOURCE_DIRS = [
    Path("source-data/sources/CDLI/images"),
    Path(
        os.path.expanduser(
            "~/Library/Mobile Documents/com~apple~CloudDocs/"
            "PROJECTS – Current Era/Glintstone Research/"
            "_archive/app-v0.1/database/images"
        )
    ),
]

ANNOTATION_RUN_SOURCE = "cdli-local-archive"
ANNOTATION_RUN_METHOD = "import"


@dataclass
class Candidate:
    p_number: str
    path: Path
    size: int


@dataclass
class CheckpointState:
    uploaded: list[str]
    skipped: list[str]
    failed: list[dict]
    started_at: str
    last_updated_at: str


# ---------------------------------------------------------------------------
# Discovery and dedup
# ---------------------------------------------------------------------------


def discover_candidates(source_dirs: list[Path]) -> dict[str, Candidate]:
    """Walk source_dirs and produce one Candidate per unique P-number.

    When the same P-number appears in multiple directories, prefer the larger
    file (likely the higher-resolution copy). Print discrepancies so the
    operator knows what was preferred.
    """
    by_p: dict[str, Candidate] = {}
    for directory in source_dirs:
        if not directory.is_dir():
            print(f"  [skip] not a directory: {directory}")
            continue
        for entry in sorted(directory.iterdir()):
            if not entry.is_file():
                continue
            if not entry.name.startswith("P") or entry.suffix.lower() not in (
                ".jpg",
                ".jpeg",
            ):
                continue
            p_number = entry.stem  # P000001
            size = entry.stat().st_size
            existing = by_p.get(p_number)
            if existing is None or size > existing.size:
                if existing is not None:
                    print(
                        f"  [dedup] {p_number}: preferring {entry} ({size}B) "
                        f"over {existing.path} ({existing.size}B)"
                    )
                by_p[p_number] = Candidate(p_number=p_number, path=entry, size=size)
            else:
                print(
                    f"  [dedup] {p_number}: keeping {existing.path} ({existing.size}B); "
                    f"skipping smaller copy at {entry} ({size}B)"
                )
    return by_p


def already_in_db(conn, p_numbers: list[str]) -> set[str]:
    """Return the subset of p_numbers that already have a row in artifact_images."""
    if not p_numbers:
        return set()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT p_number FROM artifact_images WHERE p_number = ANY(%s)",
            (p_numbers,),
        )
        return {row["p_number"] for row in cur.fetchall()}


# ---------------------------------------------------------------------------
# Run-row provenance
# ---------------------------------------------------------------------------


def ensure_annotation_run(conn) -> int:
    """Find or create the annotation_run for this batch upload.

    Returns the integer id used in artifact_images.annotation_run_id.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id FROM annotation_runs
            WHERE source_type = 'import' AND source_name = %s
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
                "Bulk import of locally-archived CDLI tablet images "
                "(attribution_raw to be backfilled by HTML-only pass).",
            ),
        )
        conn.commit()
        return cur.fetchone()["id"]


# ---------------------------------------------------------------------------
# Per-image upload
# ---------------------------------------------------------------------------


def upload_one(
    candidate: Candidate,
    storage,
    conn,
    annotation_run_id: int,
) -> Optional[int]:
    """Upload original + thumbnail to R2 and insert the DB row.

    Returns the new artifact_images.id on success, None on validation failure.
    Raises on storage / DB errors so the caller can decide to retry or abort.
    """
    data = candidate.path.read_bytes()
    if not data:
        print(f"  [fail] {candidate.p_number}: empty file")
        return None

    mime_type, _ = mimetypes.guess_type(candidate.path.name)
    mime_type = mime_type or "image/jpeg"

    try:
        dims = probe_dimensions(data)
    except Exception as e:
        print(f"  [fail] {candidate.p_number}: could not probe dimensions ({e})")
        return None

    try:
        thumb = generate_thumbnail(data)
    except Exception as e:
        print(f"  [fail] {candidate.p_number}: thumbnail generation failed ({e})")
        return None

    original_key = artifact_image_key(candidate.p_number, "photo", "local")
    thumb_key = artifact_image_key(candidate.p_number, "photo", "local", thumbnail=True)

    original_put = storage.put(
        original_key,
        data,
        content_type=mime_type,
        cache_control="public, max-age=31536000, immutable",
    )
    thumb_put = storage.put(
        thumb_key,
        thumb.bytes_,
        content_type=thumb.mime_type,
        cache_control="public, max-age=31536000, immutable",
    )

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO artifact_images
                (p_number, image_type, source_url, r2_key, r2_thumbnail_key,
                 mime_type, byte_size, width, height, sha256,
                 attribution_raw, copyright_holder, credit_line,
                 display_order, annotation_run_id)
            VALUES
                (%s, 'photo', %s, %s, %s,
                 %s, %s, %s, %s, %s,
                 NULL, NULL,
                 'Image courtesy of CDLI — credit pending verification',
                 0, %s)
            ON CONFLICT (p_number, image_type, cdli_reader_id) DO NOTHING
            RETURNING id
            """,
            (
                candidate.p_number,
                f"local:{candidate.path}",
                original_put.key,
                thumb_put.key,
                mime_type,
                original_put.byte_size,
                dims.width,
                dims.height,
                original_put.sha256,
                annotation_run_id,
            ),
        )
        row = cur.fetchone()
        artifact_image_id = row["id"] if row else None

        cur.execute(
            """
            INSERT INTO artifact_image_fetch_log
                (p_number, source_url, outcome, http_status,
                 artifact_image_id)
            VALUES (%s, %s, 'success', NULL, %s)
            """,
            (
                candidate.p_number,
                f"local:{candidate.path}",
                artifact_image_id,
            ),
        )
    conn.commit()
    return artifact_image_id


# ---------------------------------------------------------------------------
# Checkpointing
# ---------------------------------------------------------------------------


def load_checkpoint() -> CheckpointState:
    if CHECKPOINT_PATH.exists():
        with CHECKPOINT_PATH.open() as f:
            data = json.load(f)
        return CheckpointState(**data)
    now = datetime.now(timezone.utc).isoformat()
    return CheckpointState(
        uploaded=[], skipped=[], failed=[], started_at=now, last_updated_at=now
    )


def save_checkpoint(state: CheckpointState) -> None:
    state.last_updated_at = datetime.now(timezone.utc).isoformat()
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CHECKPOINT_PATH.with_suffix(".json.tmp")
    with tmp.open("w") as f:
        json.dump(asdict(state), f, indent=2)
    tmp.replace(CHECKPOINT_PATH)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--source-dir",
        action="append",
        type=Path,
        help="Source directory (repeatable). Defaults to repo + iCloud archive.",
    )
    ap.add_argument("--dry-run", action="store_true", help="Plan but do not upload.")
    ap.add_argument(
        "--delete-after-upload",
        action="store_true",
        help="Delete each source file once both uploads and DB insert succeed.",
    )
    args = ap.parse_args(argv)

    source_dirs = args.source_dir or DEFAULT_SOURCE_DIRS
    print(f"Source directories: {[str(d) for d in source_dirs]}")

    candidates = discover_candidates(source_dirs)
    print(f"Found {len(candidates)} unique P-numbers across source dirs.")
    if not candidates:
        return 0

    conn = connect_one_shot()
    try:
        skip_set = already_in_db(conn, list(candidates.keys()))
        if skip_set:
            print(f"Skipping {len(skip_set)} P-numbers already in artifact_images.")
        annotation_run_id = ensure_annotation_run(conn)
        print(f"annotation_run_id = {annotation_run_id}")

        if args.dry_run:
            for p in sorted(candidates):
                print(f"  [dry-run] would upload {p} from {candidates[p].path}")
            return 0

        storage = get_storage()
        state = load_checkpoint()
        try:
            for p_number, candidate in sorted(candidates.items()):
                if p_number in skip_set:
                    state.skipped.append(p_number)
                    save_checkpoint(state)
                    continue
                print(f"  [upload] {p_number} ({candidate.size} B)")
                try:
                    new_id = upload_one(candidate, storage, conn, annotation_run_id)
                except Exception as e:
                    print(f"  [error] {p_number}: {e}")
                    state.failed.append({"p_number": p_number, "error": str(e)})
                    save_checkpoint(state)
                    continue
                state.uploaded.append(p_number)
                save_checkpoint(state)
                if args.delete_after_upload and new_id is not None:
                    try:
                        candidate.path.unlink()
                        print(f"    deleted local {candidate.path}")
                    except OSError as e:
                        print(f"    [warn] could not delete {candidate.path}: {e}")
        finally:
            save_checkpoint(state)

        print()
        print(
            f"Done. uploaded={len(state.uploaded)} "
            f"skipped={len(state.skipped)} failed={len(state.failed)}"
        )
        if state.failed:
            print("Failures:")
            for f in state.failed:
                print(f"  - {f['p_number']}: {f['error']}")
            return 1
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
