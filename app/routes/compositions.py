"""Compositions routes — first-class browse and detail for canonical texts."""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/compositions")


@router.get("")
def compositions_list(
    request: Request,
    search: str = "",
    lang: str = "",
    genre: str = "",
    period: str = "",
    sort: str = "exemplar_count",
    limit: int = 100,
    offset: int = 0,
):
    api = request.app.state.api
    params: dict = {"limit": limit, "offset": offset}
    if search:
        params["q"] = search
    if sort:
        params["sort"] = sort

    try:
        data = api.get("/composites", params=params)
        composites = data.get("items", [])
        total = data.get("total", 0)
    except Exception:
        composites = []
        total = 0

    # Build filter sets from result data for the facets
    genres = sorted({c.get("genre") for c in composites if c.get("genre")})
    languages = sorted({c.get("language") for c in composites if c.get("language")})
    periods = sorted({c.get("period") for c in composites if c.get("period")})

    # Client-side filter (lang/genre/period filters applied post-fetch since
    # the /composites API doesn't yet support these params)
    if lang:
        composites = [
            c for c in composites if (c.get("language") or "").lower() == lang.lower()
        ]
    if genre:
        composites = [
            c for c in composites if (c.get("genre") or "").lower() == genre.lower()
        ]
    if period:
        composites = [
            c for c in composites if (c.get("period") or "").lower() == period.lower()
        ]

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "compositions/index.html",
        {
            "composites": composites,
            "total": total,
            "search": search,
            "lang": lang,
            "genre": genre,
            "period": period,
            "genres": genres,
            "languages": languages,
            "periods": periods,
            "api_url": request.app.state.api.base_url,
        },
    )


@router.get("/{q_number}")
def composition_detail(request: Request, q_number: str):
    api = request.app.state.api
    try:
        composite = api.get(f"/composites/{q_number}")
    except Exception:
        return RedirectResponse(url="/compositions", status_code=302)

    try:
        exemplars_data = api.get(f"/composites/{q_number}/exemplars")
        exemplars = (
            exemplars_data.get("items", [])
            if isinstance(exemplars_data, dict)
            else exemplars_data
        )
    except Exception:
        exemplars = []

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "compositions/detail.html",
        {
            "composite": composite,
            "exemplars": exemplars,
            "api_url": request.app.state.api.base_url,
        },
    )
