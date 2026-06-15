"""WebP thumbnail generation.

400px long-edge, quality 80, RGB-converted (drops alpha — tablet imagery is
always opaque). Pillow handles the resize.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageOps


THUMBNAIL_LONG_EDGE_PX = 400
THUMBNAIL_QUALITY = 80


@dataclass(frozen=True)
class Thumbnail:
    bytes_: bytes
    width: int
    height: int
    mime_type: str = "image/webp"


@dataclass(frozen=True)
class ImageDimensions:
    width: int
    height: int


def generate_thumbnail(original_bytes: bytes) -> Thumbnail:
    """Generate a 400px long-edge WebP thumbnail. Raises on undecodable input.

    ImageOps.exif_transpose normalizes EXIF orientation so portrait photos
    don't end up sideways.
    """
    with Image.open(io.BytesIO(original_bytes)) as im:
        # exif_transpose/convert return Image; the loop var was inferred as
        # ImageFile from Image.open. Same object family, harmless at runtime.
        im = ImageOps.exif_transpose(im)  # type: ignore[assignment]
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")  # type: ignore[assignment]
        im.thumbnail(
            (THUMBNAIL_LONG_EDGE_PX, THUMBNAIL_LONG_EDGE_PX),
            Image.Resampling.LANCZOS,
        )
        out = io.BytesIO()
        im.save(out, format="WEBP", quality=THUMBNAIL_QUALITY, method=6)
        return Thumbnail(bytes_=out.getvalue(), width=im.width, height=im.height)


def probe_dimensions(image_bytes: bytes) -> ImageDimensions:
    """Read width and height from image header without fully decoding."""
    with Image.open(io.BytesIO(image_bytes)) as im:
        return ImageDimensions(width=im.width, height=im.height)
