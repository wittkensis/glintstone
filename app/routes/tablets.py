"""Tablet routes — list and detail."""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Query, Request

from app.list_view import Page, build_filtered_list, active_filters_as_dicts
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

    page_obj = Page.from_dict(data)
    # Fall back to empty option lists when the API omits filter_options
    if not page_obj.filter_options:
        page_obj.filter_options = {
            "period": [],
            "provenience": [],
            "genre": [],
            "language": [],
        }

    lv = build_filtered_list(
        scope="tablets",
        base_path="/tablets",
        query_args={
            "search": search,
            "period": period,
            "provenience": provenience,
            "genre": genre,
            "language": language,
            # has_ocr is a flag \u2014 represent it as a non-empty string when set
            "has_ocr": "1" if has_ocr else "",
        },
        filter_dims=["period", "provenience", "genre", "language", "has_ocr"],
        page_obj=page_obj,
        preserve_params={"pipeline": pipeline} if pipeline else None,
    )

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "tablets/list.html",
        {
            "tablets": lv.items,
            "total": lv.total,
            "page": lv.page,
            "total_pages": lv.total_pages,
            "search": search,
            "pipeline": pipeline,
            "period": period,
            "provenience": provenience,
            "genre": genre,
            "language": language,
            "has_ocr": has_ocr,
            "filter_options": lv.filter_options,
            "active_filters": active_filters_as_dicts(lv),
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
            "api_url": request.app.state.api.base_url,
            "current_user": current_user,
            "saved_item_id": saved_item_id,
            "debug_json": debug_json,
            "debug_tablets_json": debug_tablets_json,
            "web_url": settings.web_url,
        },
    )
