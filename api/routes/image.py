"""GET /image — Tablet image serving. Stub for now."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/image")
def get_image(id: str | None = None):
    if not id:
        raise HTTPException(status_code=400, detail="Missing required parameter: id")

    # TODO: Implement image serving from IMAGE_PATH
    raise HTTPException(status_code=501, detail="Image serving not yet implemented")
