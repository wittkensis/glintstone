"""Scholars listing — stub page for the Browse-Scholars nav chip."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/scholars")


@router.get("")
def scholar_list(request: Request, search: str = "", page: int = 1):
    api = request.app.state.api
    try:
        data = api.get(
            "/scholars",
            params={"search": search, "page": page, "per_page": 24},
        )
    except Exception:
        data = {"items": [], "total": 0, "page": 1, "per_page": 24, "total_pages": 0}

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "scholars/list.html",
        {
            "scholars": data.get("items", []),
            "total": data.get("total", 0),
            "page": data.get("page", 1),
            "total_pages": data.get("total_pages", 0),
            "search": search,
            "api_url": request.app.state.api.base_url,
        },
    )
