"""Scholars listing — search-first directory page."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/scholars")


@router.get("")
def scholar_list(request: Request):
    # The page uses client-side search via the /api/v2/scholars endpoint.
    # We only need the grand total for the subtitle — no results fetched on load.
    api = request.app.state.api
    total_result = api.list_scholars({"per_page": 1})

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "scholars/list.html",
        {
            "total": total_result.total,
            "api_url": request.app.state.api.base_url,
        },
    )
