"""Global search proxy — serves HTML fragments to the drawer in base.html.

The web app's two-tier rule (CLAUDE.md) forbids the browser from hitting the
API directly. The drawer's JS posts here; this route proxies to /api/v2/search
and renders the matching Jinja partial.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

router = APIRouter(prefix="/_search")


SCOPE_TO_TYPES: dict[str, list[str]] = {
    "all": ["tablets", "collections", "lemmas", "signs", "scholars"],
    "tablets": ["tablets"],
    "collections": ["collections"],
    "dictionary": ["lemmas", "signs", "glosses"],
    "scholars": ["scholars"],
}

SCOPE_TO_LABEL: dict[str, str] = {
    "all": "All",
    "tablets": "Artifacts",
    "collections": "Collections",
    "dictionary": "Dictionary",
    "scholars": "Scholars",
}


NO_STORE_HEADERS = {
    # The drawer fragment can shift between empty/populated as ingestion runs;
    # we never want a browser (or intermediate cache) to keep an old answer.
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
}


@router.get("/suggest", response_class=HTMLResponse)
def suggest(
    request: Request,
    q: str = "",
    scope: str = "all",
    limit: int = 8,
):
    """Return an HTML fragment for the drawer body."""
    q = q.strip()
    if not q:
        # Empty query — JS falls back to localStorage recent searches.
        return Response(status_code=204, headers=NO_STORE_HEADERS)

    types = SCOPE_TO_TYPES.get(scope, SCOPE_TO_TYPES["all"])
    api = request.app.state.api
    try:
        envelope = api.get(
            "/search",
            params={"q": q, "types": types, "limit": limit, "mode": "hybrid"},
        )
    except Exception:
        envelope = {"data": {"groups": []}, "summary": "Search unavailable."}

    groups = (envelope.get("data") or {}).get("groups") or []

    # Surface group-display config (label + entity URL builder) in the partial
    # context so the template stays free of per-type if-ladders.
    from app.main import templates

    response = templates.TemplateResponse(
        request,
        "partials/global_search_results.html",
        {
            "groups": groups,
            "scope": scope,
            "scope_label": SCOPE_TO_LABEL.get(scope, "All"),
            "q": q,
            "api_url": request.app.state.api.base_url,
        },
    )
    for k, v in NO_STORE_HEADERS.items():
        response.headers[k] = v
    return response
