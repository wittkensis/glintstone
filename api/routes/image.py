"""GET /image/{p_number} — Tablet image serving with thumbnail support.

Per-surface serving (#129): pass ``?surface_image_id=<id>`` (the id from the
artifact's image manifest, ``GET /artifacts/{p}/images`` /
``ArtifactRepository.get_images``) to serve a *specific* surface's image —
obverse, reverse, etc. — rather than the artifact's single primary image.
Each surface image has its own pixel dimensions, and sign-annotation bounding
boxes are stored in their own surface image's coordinate space, so the viewer
must request and scale each surface independently.

When a surface image's ``image_width``/``image_height`` are still NULL, the
serving path measures the bytes once and writes them back (lazy backfill) so
subsequent overlay scaling is precise without relying on the browser's
``naturalWidth``.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from PIL import Image

from core.config import get_settings
from core.database import get_db
from api.repositories.artifact_repo import ArtifactRepository

router = APIRouter(tags=["images"])


def _resolve_path(image_dir: Path, image_path: str) -> Path | None:
    """Resolve a stored ``image_path`` to a real file on disk.

    ``surface_images.image_path`` may name either a file or a directory (the
    compvis source stores ``compvis/<P>/Obv`` style directory references). For
    a directory we take the first image file inside it.
    """
    candidate = image_dir / image_path
    if candidate.is_file():
        return candidate
    if candidate.is_dir():
        for child in sorted(candidate.iterdir()):
            if child.suffix.lower() in (".jpg", ".jpeg", ".png", ".tif", ".tiff"):
                return child
    return None


def _find_image(p_number: str, conn) -> Path | None:
    """Resolve image path: surface_images table → filesystem → None."""
    settings = get_settings()
    image_dir = Path(settings.image_path)

    # 1. Check surface_images table for primary image
    repo = ArtifactRepository(conn)
    images = repo.get_images(p_number)
    for img in images:
        if img.get("image_path"):
            resolved = _resolve_path(image_dir, img["image_path"])
            if resolved is not None:
                return resolved

    # 2. Filesystem fallback: {image_path}/{p_number}.jpg
    for ext in (".jpg", ".jpeg", ".png"):
        candidate = image_dir / f"{p_number}{ext}"
        if candidate.exists():
            return candidate

    return None


def _find_surface_image(surface_image_id: int, conn) -> Path | None:
    """Resolve a specific surface image's file, backfilling its dimensions.

    Returns the file path for the given ``surface_image_id``, and — when the
    row's stored dimensions are NULL — measures the image once and persists
    ``image_width``/``image_height`` back to ``surface_images`` (#129).
    """
    settings = get_settings()
    image_dir = Path(settings.image_path)
    repo = ArtifactRepository(conn)

    row = repo.get_surface_image(surface_image_id)
    if not row or not row.get("image_path"):
        return None

    resolved = _resolve_path(image_dir, row["image_path"])
    if resolved is None:
        return None

    if row.get("image_width") is None or row.get("image_height") is None:
        try:
            with Image.open(resolved) as img:
                width, height = img.size
            repo.set_surface_image_dimensions(surface_image_id, width, height)
        except Exception:
            # Measuring is best-effort; serving still succeeds without it.
            pass

    return resolved


def _get_thumbnail(source: Path, size: int) -> Path:
    """Generate or return cached thumbnail."""
    settings = get_settings()
    thumb_dir = Path(settings.image_path) / ".thumbs" / str(size)
    thumb_dir.mkdir(parents=True, exist_ok=True)

    thumb_path = thumb_dir / f"{source.stem}.jpg"
    if thumb_path.exists() and thumb_path.stat().st_mtime >= source.stat().st_mtime:
        return thumb_path

    with Image.open(source) as img:
        # Image.LANCZOS is a runtime-valid alias for Image.Resampling.LANCZOS;
        # the Pillow stubs only expose it on the Resampling enum.
        img.thumbnail((size, size), Image.LANCZOS)  # type: ignore[attr-defined]
        if img.mode != "RGB":
            # convert() returns Image; the loop var was inferred as ImageFile
            # from Image.open. Same object family, harmless at runtime.
            img = img.convert("RGB")  # type: ignore[assignment]
        img.save(thumb_path, "JPEG", quality=85)

    return thumb_path


@router.get("/image/{p_number}")
def get_image(
    p_number: str,
    size: int | None = None,
    surface_image_id: int | None = None,
    conn=Depends(get_db),
):
    if surface_image_id is not None:
        source = _find_surface_image(surface_image_id, conn)
    else:
        source = _find_image(p_number, conn)

    if source is None:
        raise HTTPException(status_code=404, detail="Image not found")

    if size and size > 0:
        path = _get_thumbnail(source, size)
    else:
        path = source

    media_type = "image/jpeg"
    if path.suffix.lower() == ".png":
        media_type = "image/png"

    return FileResponse(path, media_type=media_type)
