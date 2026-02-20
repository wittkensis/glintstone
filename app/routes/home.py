"""Homepage route."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/")
def homepage(request: Request):
    api = request.app.state.api

    try:
        kpi = api.get("/stats/kpi")
    except Exception:
        kpi = None

    try:
        featured = api.get("/collections/random", params={"limit": 3})
    except Exception:
        featured = []

    from app.main import templates
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "kpi": kpi,
            "featured_collections": featured,
            "api_url": request.app.state.api.base_url,
        },
    )
