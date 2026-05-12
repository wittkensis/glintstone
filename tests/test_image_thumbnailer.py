"""Unit tests for ingestion/images/thumbnailer.py."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from ingestion.images.thumbnailer import (
    THUMBNAIL_LONG_EDGE_PX,
    generate_thumbnail,
    probe_dimensions,
)


def _synthesize_jpeg(width: int, height: int) -> bytes:
    """Build a synthetic JPEG so tests don't depend on any committed fixture."""
    img = Image.new("RGB", (width, height), (120, 70, 30))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=85)
    return out.getvalue()


class TestThumbnailGeneration:
    def test_landscape_constrained_to_400px_long_edge(self) -> None:
        original = _synthesize_jpeg(1600, 800)
        thumb = generate_thumbnail(original)
        assert thumb.width == THUMBNAIL_LONG_EDGE_PX
        assert thumb.height == THUMBNAIL_LONG_EDGE_PX // 2
        assert thumb.mime_type == "image/webp"

    def test_portrait_constrained_to_400px_long_edge(self) -> None:
        original = _synthesize_jpeg(800, 1600)
        thumb = generate_thumbnail(original)
        assert thumb.height == THUMBNAIL_LONG_EDGE_PX
        assert thumb.width == THUMBNAIL_LONG_EDGE_PX // 2

    def test_already_small_image_is_not_upscaled(self) -> None:
        original = _synthesize_jpeg(200, 150)
        thumb = generate_thumbnail(original)
        assert thumb.width == 200
        assert thumb.height == 150

    def test_output_is_webp_decodable(self) -> None:
        original = _synthesize_jpeg(800, 600)
        thumb = generate_thumbnail(original)
        decoded = Image.open(io.BytesIO(thumb.bytes_))
        assert decoded.format == "WEBP"
        assert decoded.mode in ("RGB", "RGBA")

    def test_undecodable_input_raises(self) -> None:
        with pytest.raises(Exception):
            generate_thumbnail(b"this is not an image")


class TestProbeDimensions:
    def test_returns_actual_dimensions(self) -> None:
        original = _synthesize_jpeg(1280, 720)
        dims = probe_dimensions(original)
        assert dims.width == 1280
        assert dims.height == 720
