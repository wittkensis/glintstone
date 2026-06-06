"""Scholars listing — stub page for the Browse-Scholars nav chip."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/scholars")


@router.get("")
def scholar_list(request: Request, search: str = "", page: int = 1):
    api = request.app.state.api
    scholar_page = api.list_scholars({"search": search, "page": page, "per_page": 24})

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "scholars/list.html",
        {
            "scholars": scholar_page.items,
            "total": scholar_page.total,
            "page": scholar_page.page,
            "total_pages": scholar_page.total_pages,
            "search": search,
            "api_url": request.app.state.api.base_url,
        },
    )
