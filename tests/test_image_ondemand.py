"""Unit tests for api/services/image_ondemand.py.

These exercise the orchestration logic without hitting CDLI, R2, or
Postgres — fetch, storage, and the DB connection are all replaced with
fakes. Integration with real services is verified by the smoke-test path
documented in ops/scripts/upload_local_images.py and the in-prod runs
on 2026-05-12.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Callable, Optional
from unittest.mock import patch

from PIL import Image

from api.services.image_ondemand import (
    EnsureResult,
    _per_artifact_lock,
    ensure_images_for_artifact,
)


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


def _synthetic_jpeg(width: int = 800, height: int = 600) -> bytes:
    img = Image.new("RGB", (width, height), (50, 50, 50))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=80)
    return out.getvalue()


@dataclass
class _FakeFetchResult:
    status_code: int
    body: bytes
    content_type: Optional[str] = "image/jpeg"
    final_url: str = ""


class _FakeCursor:
    def __init__(self, parent: "_FakeConn") -> None:
        self.parent = parent
        self._last_result: list[dict] = []

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *_a) -> None:
        return None

    def execute(self, sql: str, params=None) -> None:
        self.parent.queries.append((sql.strip().split()[0].upper(), sql, params))
        sql_lower = sql.strip().lower()
        # COUNT existing rows
        if "select count(*) as n from artifact_images" in sql_lower:
            self._last_result = [{"n": self.parent.existing_rows}]
            return
        # Look up annotation run
        if "from annotation_runs" in sql_lower and sql_lower.startswith("select"):
            self._last_result = (
                [{"id": self.parent.annotation_run_id}]
                if self.parent.annotation_run_exists
                else []
            )
            return
        # Insert annotation_runs -> RETURNING id
        if sql_lower.startswith("insert into annotation_runs"):
            self.parent.annotation_run_id = 999
            self.parent.annotation_run_exists = True
            self._last_result = [{"id": 999}]
            return
        # INSERT into artifact_images RETURNING id
        if sql_lower.startswith("insert into artifact_images"):
            self.parent.inserted_rows += 1
            self._last_result = [{"id": 100 + self.parent.inserted_rows}]
            return
        # INSERT into artifact_image_fetch_log (no RETURNING)
        if sql_lower.startswith("insert into artifact_image_fetch_log"):
            self.parent.log_entries += 1
            self._last_result = []
            return
        self._last_result = []

    def fetchone(self):
        return self._last_result[0] if self._last_result else None

    def fetchall(self):
        return self._last_result


class _FakeConn:
    def __init__(self, existing_rows: int = 0) -> None:
        self.existing_rows = existing_rows
        self.annotation_run_id = 42
        self.annotation_run_exists = True
        self.inserted_rows = 0
        self.log_entries = 0
        self.commits = 0
        self.queries: list = []

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self)

    def commit(self) -> None:
        self.commits += 1


class _FakeStorage:
    def __init__(self) -> None:
        self.puts: list[tuple[str, int]] = []

    def put(self, key, data, *, content_type, cache_control=None):
        from core.storage import PutResult, _sha256

        self.puts.append((key, len(data)))
        return PutResult(key=key, sha256=_sha256(data), byte_size=len(data))

    def exists(self, key: str) -> bool:
        return any(k == key for k, _ in self.puts)

    def public_url(self, key: str) -> str:
        return f"fake://{key}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _patch_pipeline(
    html_status: int,
    html_body: bytes,
    image_status: int,
    image_body: bytes,
) -> Callable:
    """Returns a context-managing patcher that replaces fetch + get_storage."""
    storage = _FakeStorage()
    call_count = {"n": 0}

    def fake_fetch(url, *, respect_crawl_delay, **kwargs):
        call_count["n"] += 1
        # First call is the artifact HTML page, subsequent are image binaries.
        if call_count["n"] == 1:
            return _FakeFetchResult(
                status_code=html_status,
                body=html_body,
                content_type="text/html",
                final_url=url,
            )
        return _FakeFetchResult(
            status_code=image_status,
            body=image_body,
            content_type="image/jpeg",
            final_url=url,
        )

    return (
        patch("api.services.image_ondemand.fetch", side_effect=fake_fetch),
        patch("api.services.image_ondemand.get_storage", return_value=storage),
        storage,
    )


_SAMPLE_HTML_P000001 = b"""
<html><body>
  <div class="visual-asset">
    <a href="/artifacts/1/reader/88909">
      <img src="/dl/tn_photo/P000001.jpg" alt="photo" />
    </a>
    <p>&copy; Vorderasiatisches Museum, Berlin, Germany</p>
  </div>
</body></html>
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEnsureCachedShortCircuit:
    def test_existing_rows_skip_fetch(self) -> None:
        conn = _FakeConn(existing_rows=2)
        with (
            patch("api.services.image_ondemand.fetch") as mocked_fetch,
            patch("api.services.image_ondemand.get_storage"),
        ):
            result = ensure_images_for_artifact(conn, "P000001")
        assert result == EnsureResult(status="cached", image_count=2)
        mocked_fetch.assert_not_called()


class TestEnsureFetchSuccess:
    def test_happy_path_fetches_html_image_thumbnail_inserts_row(self) -> None:
        conn = _FakeConn(existing_rows=0)
        jpg = _synthetic_jpeg()
        fetch_patch, storage_patch, storage = _patch_pipeline(
            html_status=200,
            html_body=_SAMPLE_HTML_P000001,
            image_status=200,
            image_body=jpg,
        )
        with fetch_patch, storage_patch:
            result = ensure_images_for_artifact(conn, "P000001")
        assert result.status == "fetched"
        assert result.image_count == 1
        # Should have uploaded original + thumbnail to storage
        assert len(storage.puts) == 2
        keys = [k for k, _ in storage.puts]
        assert any(k.endswith(".jpg") for k in keys)
        assert any(k.endswith("-thumb.webp") for k in keys)
        # Inserted one artifact_images row + at least one fetch_log entry
        assert conn.inserted_rows == 1
        assert conn.log_entries >= 1


class TestEnsureFetchFailures:
    def test_html_404_returns_not_found(self) -> None:
        conn = _FakeConn(existing_rows=0)
        fetch_patch, storage_patch, _ = _patch_pipeline(
            html_status=404,
            html_body=b"",
            image_status=200,
            image_body=b"",
        )
        with fetch_patch, storage_patch:
            result = ensure_images_for_artifact(conn, "P999999")
        assert result.status == "not_found_at_cdli"
        assert result.image_count == 0
        assert conn.inserted_rows == 0

    def test_html_5xx_returns_fetch_error(self) -> None:
        conn = _FakeConn(existing_rows=0)
        fetch_patch, storage_patch, _ = _patch_pipeline(
            html_status=503,
            html_body=b"",
            image_status=200,
            image_body=b"",
        )
        with fetch_patch, storage_patch:
            result = ensure_images_for_artifact(conn, "P000001")
        assert result.status == "fetch_error"
        assert "503" in (result.detail or "")

    def test_image_404_logs_but_does_not_insert(self) -> None:
        conn = _FakeConn(existing_rows=0)
        fetch_patch, storage_patch, storage = _patch_pipeline(
            html_status=200,
            html_body=_SAMPLE_HTML_P000001,
            image_status=404,
            image_body=b"",
        )
        with fetch_patch, storage_patch:
            result = ensure_images_for_artifact(conn, "P000001")
        # Manifest had 1 image; binary 404'd; no row inserted but logged
        assert result.image_count == 0
        assert conn.inserted_rows == 0
        assert conn.log_entries >= 1
        assert len(storage.puts) == 0


class TestEnsureNoImagesOnPage:
    def test_empty_manifest_returns_not_found(self) -> None:
        conn = _FakeConn(existing_rows=0)
        fetch_patch, storage_patch, _ = _patch_pipeline(
            html_status=200,
            html_body=b"<html><body><p>no images</p></body></html>",
            image_status=200,
            image_body=b"",
        )
        with fetch_patch, storage_patch:
            result = ensure_images_for_artifact(conn, "P000001")
        assert result.status == "not_found_at_cdli"
        assert conn.inserted_rows == 0


class TestLockReuse:
    def test_same_p_number_returns_same_lock(self) -> None:
        # Two requests for the same artifact share the same lock instance,
        # so a second concurrent caller queues behind the first.
        lock_a = _per_artifact_lock("P000123")
        lock_b = _per_artifact_lock("P000123")
        assert lock_a is lock_b

    def test_different_p_numbers_get_distinct_locks(self) -> None:
        lock_a = _per_artifact_lock("P000123")
        lock_b = _per_artifact_lock("P000456")
        assert lock_a is not lock_b
