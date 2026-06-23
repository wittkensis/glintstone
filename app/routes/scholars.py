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
def scholar_detail(
    scholar_id: int,
    request: Request,
    type: str = "",
    pub_page: int = 1,
    contrib_page: int = 1,
):
    # Registered after the list route so it doesn't shadow GET "" — FastAPI
    # matches by registration order and "" is declared first.
    api = request.app.state.api

    scholar = api.get_scholar(scholar_id)
    if not scholar:
        # get_scholar degrades to {} on a 404 (or any error) from the API.
        # A missing scholar is a genuine not-found; raise so the global
        # exception handler serves the standard errors/404 page.
        raise HTTPException(status_code=404, detail="Scholar not found")

    # Publications & works (#206) — the richer surface, rendered first per the
    # spec default. First 50 rows, most-cited first. The ?type= query narrows
    # the row list to one publication_type (shareable URL, back-button works);
    # the stat strip and pill counts stay whole-corpus. The client degrades to
    # an explicit-empty envelope on failure, so a works-fetch error renders the
    # #189 "No publications on record" panel rather than blanking the page.
    pub_params: dict = {"per_page": 50, "page": max(1, pub_page)}
    if type.strip():
        pub_params["type"] = type.strip()
    publications = api.get_scholar_publications(scholar_id, pub_params)

    # Contributions ledger (#177) — newest annotation run first, 50/page. The
    # ?contrib_page= query param drives server-rendered "Show more" pagination,
    # mirroring the publications ?pub_page= pattern (#206) for consistency. Both
    # paged params live on the same URL, so advancing one preserves the other.
    contributions = api.get_scholar_contributions(
        scholar_id, {"per_page": 50, "page": max(1, contrib_page)}
    )

    # Activity profile (#157) — a compact view of *when* (which historical
    # periods) and *how* (which roles) this scholar contributed. Non-fatal: the
    # client degrades to {} on failure, so an activity-fetch error renders the
    # widget's empty state rather than blanking the page.
    activity = api.get_scholar_activity(scholar_id)

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "scholars/detail.html",
        {
            "scholar": scholar,
            "activity": activity,
            "publications": publications.get("items", []),
            "pub_total": publications.get("total", 0),
            "pub_summary": publications.get("summary", {}),
            "pub_type_counts": publications.get("type_counts", []),
            "pub_active_type": publications.get("type", ""),
            "pub_page": publications.get("page", 1),
            "pub_total_pages": publications.get("total_pages", 0),
            "contributions": contributions.items,
            "contrib_total": contributions.total,
            "run_count": contributions.run_count,
            "contrib_page": contributions.page,
            "contrib_total_pages": contributions.total_pages,
            "pub_active_type_for_contrib": type.strip(),
        },
    )
