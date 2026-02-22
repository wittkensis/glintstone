"""GET /image/{p_number} — Tablet image serving with thumbnail support."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from PIL import Image

from core.config import get_settings
from core.database import get_db
from api.repositories.artifact_repo import ArtifactRepository

router = APIRouter(tags=["images"])


def _find_image(p_number: str, conn) -> Path | None:
    """Resolve image path: surface_images table → filesystem → None."""
    settings = get_settings()
    image_dir = Path(settings.image_path)

    # 1. Check surface_images table for primary image
    repo = ArtifactRepository(conn)
    images = repo.get_images(p_number)
    for img in images:
        if img.get("image_path"):
            candidate = image_dir / img["image_path"]
            if candidate.exists():
                return candidate

    # 2. Filesystem fallback: {image_path}/{p_number}.jpg
    for ext in (".jpg", ".jpeg", ".png"):
        candidate = image_dir / f"{p_number}{ext}"
        if candidate.exists():
            return candidate

    return None


def _get_thumbnail(source: Path, size: int) -> Path:
    """Generate or return cached thumbnail."""
    settings = get_settings()
    thumb_dir = Path(settings.image_path) / ".thumbs" / str(size)
    thumb_dir.mkdir(parents=True, exist_ok=True)

    thumb_path = thumb_dir / f"{source.stem}.jpg"
    if thumb_path.exists() and thumb_path.stat().st_mtime >= source.stat().st_mtime:
        return thumb_path

    with Image.open(source) as img:
        img.thumbnail((size, size), Image.LANCZOS)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(thumb_path, "JPEG", quality=85)

    return thumb_path


@router.get("/image/{p_number}")
def get_image(p_number: str, size: int | None = None, conn=Depends(get_db)):
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
