"""Tablet routes — list and detail."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/tablets")


@router.get("")
def tablet_list(request: Request, search: str = "", pipeline: str = "", page: int = 1):
    api = request.app.state.api
    params = {"page": page, "per_page": 24}
    if search:
        params["search"] = search
    if pipeline:
        params["pipeline"] = pipeline

    try:
        data = api.get("/artifacts", params=params)
    except Exception:
        data = {"items": [], "total": 0, "page": 1, "per_page": 24, "total_pages": 0}

    from app.main import templates
    return templates.TemplateResponse(
        "tablets/list.html",
        {
            "request": request,
            "tablets": data.get("items", []),
            "total": data.get("total", 0),
            "page": data.get("page", 1),
            "total_pages": data.get("total_pages", 0),
            "search": search,
            "pipeline": pipeline,
            "api_url": request.app.state.api.base_url,
        },
    )


@router.get("/{p_number}")
def tablet_detail(request: Request, p_number: str):
    api = request.app.state.api

    try:
        tablet = api.get(f"/artifacts/{p_number}")
    except Exception:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/tablets", status_code=302)

    from app.main import templates
    return templates.TemplateResponse(
        "tablets/detail.html",
        {
            "request": request,
            "tablet": tablet,
            "api_url": request.app.state.api.base_url,
        },
    )
