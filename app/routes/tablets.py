"""Tablet routes — list and detail."""

import json
import logging
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Query, Request

from core.config import get_settings

_DEBUG_TABLETS_PATH = Path(__file__).resolve().parents[2] / "debug-tablets.json"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tablets")


@router.get("")
def tablet_list(
    request: Request,
    search: str = "",
    pipeline: str = "",
    period: list[str] = Query(default=[]),
    provenience: list[str] = Query(default=[]),
    genre: list[str] = Query(default=[]),
    language: list[str] = Query(default=[]),
    has_ocr: str = "",
    page: int = 1,
):
    api = request.app.state.api
    # include_filter_options=true lets the API return both the page and the
    # cross-filter counts in a single round trip — half the latency of two
    # sequential httpx calls.
    params: dict = {"page": page, "per_page": 24, "include_filter_options": "true"}
    if search:
        params["search"] = search
    if pipeline:
        params["pipeline"] = pipeline
    if period:
        params["period"] = period
    if provenience:
        params["provenience"] = provenience
    if genre:
        params["genre"] = genre
    if language:
        params["language"] = language
    if has_ocr:
        params["has_ocr"] = "true"

    try:
        data = api.get("/artifacts", params=params)
    except Exception:
        data = {"items": [], "total": 0, "page": 1, "per_page": 24, "total_pages": 0}

    filter_options = data.get("filter_options") or {
        "period": [],
        "provenience": [],
        "genre": [],
        "language": [],
    }

    # Build active filter pills with remove-URLs
    all_params: list[tuple[str, str]] = []
    if search:
        all_params.append(("search", search))
    for p in period:
        all_params.append(("period", p))
    for p in provenience:
        all_params.append(("provenience", p))
    for g in genre:
        all_params.append(("genre", g))
    for lang in language:
        all_params.append(("language", lang))
    if has_ocr:
        all_params.append(("has_ocr", "1"))

    _PILL_LABELS = {"has_ocr": "Has ML/OCR"}

    def _pill_label(key: str, val: str) -> str:
        if key in _PILL_LABELS:
            return _PILL_LABELS[key]
        if key == "search":
            return f"\u201c{val}\u201d"
        return val

    active_filters: list[dict] = []
    for i, (key, val) in enumerate(all_params):
        remaining = [
            f"{k}={quote(v, safe='')}" for j, (k, v) in enumerate(all_params) if j != i
        ]
        if pipeline:
            remaining.append(f"pipeline={pipeline}")
        qs = "&".join(remaining)
        remove_url = f"/tablets?{qs}" if qs else "/tablets"
        active_filters.append(
            {
                "dimension": key,
                "label": _pill_label(key, val),
                "remove_url": remove_url,
            }
        )

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "tablets/list.html",
        {
            "tablets": data.get("items", []),
            "total": data.get("total", 0),
            "page": data.get("page", 1),
            "total_pages": data.get("total_pages", 0),
            "search": search,
            "pipeline": pipeline,
            "period": period,
            "provenience": provenience,
            "genre": genre,
            "language": language,
            "has_ocr": has_ocr,
            "filter_options": filter_options,
            "active_filters": active_filters,
            "api_url": request.app.state.api.base_url,
        },
    )


@router.get("/{p_number}")
def tablet_detail(request: Request, p_number: str):
    import httpx

    api = request.app.state.api

    try:
        tablet = api.get(f"/artifacts/{p_number}")
    except Exception:
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/tablets", status_code=302)

    # Back navigation — use ?back= param if present, else Referer header, else /tablets.
    # The ?back= param takes precedence so links can bake in the exact return URL
    # (e.g. search with filters preserved). Referer is the fallback for direct JS
    # navigations that don't set the param. We only accept /tablets* paths to
    # avoid open-redirect abuse.
    back_param = request.query_params.get("back", "")
    if back_param.startswith("/tablets"):
        back_url = back_param
    else:
        referer = request.headers.get("referer", "")
        # request.base_url is a Starlette URL object; .hostname gives the host string.
        host = request.base_url.hostname or ""
        # Strip scheme+host to get path — split on host and take everything after.
        if host and host in referer and "/tablets" in referer:
            # e.g. "http://localhost:8000/tablets?search=foo" → "/tablets?search=foo"
            back_url = "/" + referer.split(host, 1)[-1].lstrip("/")
        else:
            back_url = "/tablets"

    # Auth-aware bookmark state
    current_user = None
    saved_item_id = None
    token = request.cookies.get("session_token")
    if token:
        try:
            current_user = api.get("/auth/me", token=token)
            items = api.get(
                "/users/me/saved-items",
                params={"item_type": "artifact"},
                token=token,
            )
            for item in items:
                if item.get("item_id") == p_number:
                    saved_item_id = item["id"]
                    break
        except httpx.HTTPStatusError:
            pass

    # Debug: full data dump + tablet navigation list
    debug_json = None
    debug_tablets_json = None
    settings = get_settings()
    if settings.app_debug:
        try:
            debug_data = api.get(f"/artifacts/{p_number}/debug")
            debug_json = json.dumps(debug_data, default=str, ensure_ascii=False)
        except Exception as e:
            logger.warning("Debug fetch failed for %s: %s", p_number, e)
            debug_json = None

        try:
            debug_tablets_json = _DEBUG_TABLETS_PATH.read_text()
        except FileNotFoundError:
            debug_tablets_json = None

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "tablets/detail.html",
        {
            "tablet": tablet,
            "p_number": p_number,
            "back_url": back_url,
            "api_url": request.app.state.api.base_url,
            "current_user": current_user,
            "saved_item_id": saved_item_id,
            "debug_json": debug_json,
            "debug_tablets_json": debug_tablets_json,
            "web_url": settings.web_url,
        },
    )
