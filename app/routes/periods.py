"""Canonical-periods proxy — serves the period canon JSON to the timeline JS.

The web app's two-tier rule (CLAUDE.md) forbids the browser from hitting the
API directly. The transmission timeline on composition detail pages fetches
the period canon (canonical name + BCE date range per period) to position
exemplars on a proportional BCE axis; this route proxies that single GET to
/api/v2/periods and returns the JSON unchanged.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/_periods")


@router.get("")
def list_periods(request: Request) -> JSONResponse:
    """Return the canonical-periods envelope the timeline JS expects.

    Shape: {"items": [{canonical, date_start_bce, date_end_bce, sort_order,
    group_name}, ...]}. get_periods() degrades to {"items": []} on any error,
    so the browser always receives valid JSON.
    """
    api = request.app.state.api
    return JSONResponse(api.get_periods())
