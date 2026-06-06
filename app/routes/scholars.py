"""Scholars listing — browse-scholars nav chip."""

from fastapi import APIRouter, Request

from app.list_view import Page, build_filtered_list, active_filters_as_dicts

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

    page_obj = Page.from_dict(data)
    # Scholars has no dimension filters — only free-text search.
    # build_filtered_list still handles the search pill so the pattern is uniform.
    lv = build_filtered_list(
        scope="scholars",
        base_path="/scholars",
        query_args={"search": search},
        filter_dims=[],
        page_obj=page_obj,
    )

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "scholars/list.html",
        {
            "scholars": lv.items,
            "total": lv.total,
            "page": lv.page,
            "total_pages": lv.total_pages,
            "search": search,
            "active_filters": active_filters_as_dicts(lv),
            "api_url": request.app.state.api.base_url,
        },
    )
