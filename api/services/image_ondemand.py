"""On-demand image cache fill.

When a user views an artifact whose images aren't yet in R2 + ``artifact_images``,
this service fetches the CDLI artifact page, parses the image manifest,
downloads each image binary, generates a WebP thumbnail, uploads both to R2,
and inserts an ``artifact_images`` row. Subsequent requests serve from R2.

A per-artifact lock prevents two concurrent first-view requests from racing
to fetch the same artifact twice — the second request waits for the first.

Rate limit is the 5-second courtesy floor (the same one
``ingestion/images/fetcher.py`` enforces process-wide). On-demand requests
should never trigger the 60s ``respect_crawl_delay`` mode — that's reserved
for the batch crawler.
"""

from __future__ import annotations

import mimetypes
import threading
from dataclasses import dataclass
from typing import Optional

from core.storage import artifact_image_key, get_storage
from ingestion.images.fetcher import FetchError, fetch
from ingestion.images.parser import (
    build_credit_line,
    derive_copyright_holder,
    parse_artifact_page,
)
from ingestion.images.thumbnailer import generate_thumbnail, probe_dimensions


ANNOTATION_RUN_SOURCE = "cdli-on-demand"
ANNOTATION_RUN_METHOD = "api_fetch"


_locks_guard = threading.Lock()
_locks: dict[str, threading.Lock] = {}


def _per_artifact_lock(p_number: str) -> threading.Lock:
    """Reusable per-artifact lock so concurrent ensures of the same artifact
    queue up instead of racing.
    """
    with _locks_guard:
        lock = _locks.get(p_number)
        if lock is None:
            lock = threading.Lock()
            _locks[p_number] = lock
        return lock


@dataclass(frozen=True)
class EnsureResult:
    status: str  # 'cached', 'fetched', 'not_found_at_cdli', 'fetch_error'
    image_count: int
    detail: Optional[str] = None


def ensure_images_for_artifact(
    conn, p_number: str, *, respect_crawl_delay: bool = False
) -> EnsureResult:
    """Idempotently make sure artifact_images has rows for this P-number.

    Returns immediately if rows already exist (status='cached'). Otherwise
    holds the per-artifact lock for the duration of the fetch — second
    callers will block until the first finishes, then see 'cached'.

    ``respect_crawl_delay``: pass ``True`` for batch crawlers so the fetch
    honors CDLI's robots.txt 60s Crawl-delay. On-demand traffic (the API
    default) uses the shorter 5s courtesy floor.
    """
    lock = _per_artifact_lock(p_number)
    with lock:
        existing = _count_existing(conn, p_number)
        if existing:
            return EnsureResult(status="cached", image_count=existing)

        try:
            result = fetch(
                f"https://cdli.earth/{p_number}",
                respect_crawl_delay=respect_crawl_delay,
            )
        except FetchError as e:
            return EnsureResult(status="fetch_error", image_count=0, detail=str(e))
        if result.status_code == 404:
            return EnsureResult(status="not_found_at_cdli", image_count=0)
        if result.status_code != 200:
            return EnsureResult(
                status="fetch_error",
                image_count=0,
                detail=f"HTTP {result.status_code} for {p_number} page",
            )

        manifest = parse_artifact_page(
            result.body.decode("utf-8", errors="replace"), p_number
        )
        if not manifest.images:
            return EnsureResult(status="not_found_at_cdli", image_count=0)

        annotation_run_id = _ensure_annotation_run(conn)
        storage = get_storage()
        inserted = 0
        for display_order, ref in enumerate(manifest.images):
            try:
                inserted += _fetch_and_store_one(
                    conn=conn,
                    storage=storage,
                    p_number=p_number,
                    ref=ref,
                    display_order=display_order,
                    annotation_run_id=annotation_run_id,
                    respect_crawl_delay=respect_crawl_delay,
                )
            except Exception as e:
                _log_fetch_outcome(
                    conn,
                    p_number=p_number,
                    source_url=ref.full_url,
                    outcome="other_error",
                    http_status=None,
                    error_message=str(e),
                    artifact_image_id=None,
                )
        return EnsureResult(status="fetched", image_count=inserted)


def _count_existing(conn, p_number: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS n FROM artifact_images WHERE p_number = %s",
            (p_number,),
        )
        row = cur.fetchone()
    return row["n"] if row else 0


def _ensure_annotation_run(conn) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id FROM annotation_runs
            WHERE source_type = 'import' AND source_name = %s AND method = %s
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
                "On-demand CDLI image fetch triggered by API request.",
            ),
        )
        new_id = cur.fetchone()["id"]
    conn.commit()
    return new_id


def _fetch_and_store_one(
    conn,
    storage,
    p_number: str,
    ref,
    display_order: int,
    annotation_run_id: int,
    respect_crawl_delay: bool = False,
) -> int:
    """Fetch one image binary, generate thumb, upload, insert. Returns 1 on insert."""
    try:
        bin_result = fetch(ref.full_url, respect_crawl_delay=respect_crawl_delay)
    except FetchError as e:
        _log_fetch_outcome(
            conn,
            p_number=p_number,
            source_url=ref.full_url,
            outcome="other_error",
            http_status=None,
            error_message=str(e),
            artifact_image_id=None,
        )
        return 0
    if bin_result.status_code == 404:
        _log_fetch_outcome(
            conn,
            p_number=p_number,
            source_url=ref.full_url,
            outcome="http_404",
            http_status=404,
            error_message=None,
            artifact_image_id=None,
        )
        return 0
    if bin_result.status_code != 200:
        _log_fetch_outcome(
            conn,
            p_number=p_number,
            source_url=ref.full_url,
            outcome=("http_5xx" if bin_result.status_code >= 500 else "other_error"),
            http_status=bin_result.status_code,
            error_message=None,
            artifact_image_id=None,
        )
        return 0

    data = bin_result.body
    try:
        dims = probe_dimensions(data)
        thumb = generate_thumbnail(data)
    except Exception as e:
        _log_fetch_outcome(
            conn,
            p_number=p_number,
            source_url=ref.full_url,
            outcome="decode_failed",
            http_status=None,
            error_message=str(e),
            artifact_image_id=None,
        )
        return 0

    mime_type, _ = mimetypes.guess_type(ref.full_url)
    mime_type = mime_type or bin_result.content_type or "image/jpeg"

    suffix = str(ref.cdli_reader_id) if ref.cdli_reader_id is not None else "primary"
    original_key = artifact_image_key(p_number, ref.image_type, suffix)
    thumb_key = artifact_image_key(p_number, ref.image_type, suffix, thumbnail=True)

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
                (p_number, image_type, cdli_reader_id, source_url,
                 r2_key, r2_thumbnail_key,
                 mime_type, byte_size, width, height, sha256,
                 copyright_holder, license, attribution_raw, credit_line,
                 display_order, annotation_run_id)
            VALUES
                (%(p)s, %(t)s, %(rid)s, %(src)s,
                 %(rk)s, %(tk)s,
                 %(mt)s, %(bs)s, %(w)s, %(h)s, %(sha)s,
                 %(ch)s, NULL, %(ar)s, %(cl)s,
                 %(do)s, %(arn)s)
            ON CONFLICT (p_number, image_type, cdli_reader_id) DO NOTHING
            RETURNING id
            """,
            {
                "p": p_number,
                "t": ref.image_type,
                "rid": ref.cdli_reader_id,
                "src": ref.full_url,
                "rk": original_put.key,
                "tk": thumb_put.key,
                "mt": mime_type,
                "bs": original_put.byte_size,
                "w": dims.width,
                "h": dims.height,
                "sha": original_put.sha256,
                "ch": derive_copyright_holder(ref.attribution_raw),
                "ar": ref.attribution_raw,
                "cl": build_credit_line(ref.attribution_raw),
                "do": display_order,
                "arn": annotation_run_id,
            },
        )
        row = cur.fetchone()
        artifact_image_id = row["id"] if row else None

    _log_fetch_outcome(
        conn,
        p_number=p_number,
        source_url=ref.full_url,
        outcome="success",
        http_status=200,
        error_message=None,
        artifact_image_id=artifact_image_id,
    )
    conn.commit()
    return 1 if artifact_image_id else 0


def _log_fetch_outcome(
    conn,
    *,
    p_number: str,
    source_url: str,
    outcome: str,
    http_status: Optional[int],
    error_message: Optional[str],
    artifact_image_id: Optional[int],
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO artifact_image_fetch_log
                (p_number, source_url, outcome, http_status, error_message, artifact_image_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                p_number,
                source_url,
                outcome,
                http_status,
                error_message,
                artifact_image_id,
            ),
        )
    conn.commit()
