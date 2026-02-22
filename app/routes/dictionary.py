"""Dictionary route — placeholder."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/dictionary")


@router.get("")
def dictionary_index(request: Request):
    """Dictionary browser page."""
    api = request.app.state.api

    # Fetch grouping counts for sidebar
    try:
        counts = api.get("/dictionary/counts")
    except Exception:
        counts = {"all": 0, "pos": {}, "language": {}, "frequency": {}}

    from app.main import templates

    return templates.TemplateResponse(
        "dictionary/index.html",
        {
            "request": request,
            "counts": counts,
            "api_url": request.app.state.api.base_url,
        },
    )
