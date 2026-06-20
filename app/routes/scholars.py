"""Scholars listing — search-first directory page + record detail."""

from fastapi import APIRouter, HTTPException, Request

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


@router.get("/{scholar_id}")
def scholar_detail(scholar_id: int, request: Request):
    # Registered after the list route so it doesn't shadow GET "" — FastAPI
    # matches by registration order and "" is declared first.
    api = request.app.state.api

    scholar = api.get_scholar(scholar_id)
    if not scholar:
        # get_scholar degrades to {} on a 404 (or any error) from the API.
        # A missing scholar is a genuine not-found; raise so the global
        # exception handler serves the standard errors/404 page.
        raise HTTPException(status_code=404, detail="Scholar not found")

    # First 50 contributions, newest annotation run first. Pagination beyond
    # the first page is a deliberate fast-follow (#157), not built here.
    contributions = api.get_scholar_contributions(scholar_id, {"per_page": 50})

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "scholars/detail.html",
        {
            "scholar": scholar,
            "contributions": contributions.items,
            "contrib_total": contributions.total,
            "run_count": contributions.run_count,
        },
    )
