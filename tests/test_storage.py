"""Unit tests for core/storage.py."""

from __future__ import annotations

import hashlib
from pathlib import Path

from core.storage import (
    LocalFilesystemStorage,
    _resolve_r2_secret,
    artifact_image_key,
)


class TestKeyHelper:
    def test_original_key_has_extension(self) -> None:
        assert (
            artifact_image_key("P000001", "photo", "local")
            == "tablets/P000001/photo-local.jpg"
        )

    def test_thumbnail_key_is_webp(self) -> None:
        assert (
            artifact_image_key("P000001", "photo", "local", thumbnail=True)
            == "tablets/P000001/photo-local-thumb.webp"
        )

    def test_extension_override(self) -> None:
        assert (
            artifact_image_key("P000001", "lineart", "4", extension="png")
            == "tablets/P000001/lineart-4.png"
        )

    def test_extension_dot_is_stripped(self) -> None:
        # .jpg and jpg should produce the same key — strip leading dot
        assert artifact_image_key(
            "P000001", "photo", "x", extension=".jpg"
        ) == artifact_image_key("P000001", "photo", "x", extension="jpg")


class TestResolveR2Secret:
    def test_cfat_prefixed_value_is_sha256_hashed(self) -> None:
        # Cloudflare R2 token format: raw value is cfat_*; the actual S3
        # Secret Access Key is the SHA-256 hex of that value.
        raw = "cfat_example_token_value_12345"
        resolved = _resolve_r2_secret(raw)
        assert resolved == hashlib.sha256(raw.encode()).hexdigest()
        assert len(resolved) == 64
        assert resolved != raw

    def test_hex_secret_passes_through_unchanged(self) -> None:
        # 64-hex S3 secrets (the legacy / direct format) shouldn't be hashed.
        hex_secret = "a" * 64
        assert _resolve_r2_secret(hex_secret) == hex_secret


class TestLocalFilesystemStorage:
    def test_put_then_read(self, tmp_path: Path) -> None:
        storage = LocalFilesystemStorage(root=tmp_path)
        result = storage.put("foo/bar.txt", b"hello", content_type="text/plain")
        assert result.key == "foo/bar.txt"
        assert result.byte_size == 5
        assert result.sha256 == hashlib.sha256(b"hello").hexdigest()
        assert (tmp_path / "foo" / "bar.txt").read_bytes() == b"hello"

    def test_exists(self, tmp_path: Path) -> None:
        storage = LocalFilesystemStorage(root=tmp_path)
        storage.put("a/b.bin", b"x", content_type="application/octet-stream")
        assert storage.exists("a/b.bin") is True
        assert storage.exists("missing.bin") is False

    def test_public_url(self, tmp_path: Path) -> None:
        storage = LocalFilesystemStorage(root=tmp_path, public_base_url="/assets")
        assert storage.public_url("foo/bar.jpg") == "/assets/foo/bar.jpg"

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        storage = LocalFilesystemStorage(root=tmp_path)
        # Nested key — parent must be created on demand
        storage.put("a/b/c/deep.bin", b"y", content_type="application/octet-stream")
        assert (tmp_path / "a" / "b" / "c" / "deep.bin").exists()
