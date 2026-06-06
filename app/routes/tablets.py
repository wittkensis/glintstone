"""Tablet routes — list and detail."""

import json
import logging
from pathlib import Path
from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse

from app.list_view import active_filters_as_dicts, build_filtered_list
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

    artifact_page = api.list_artifacts(params)

    lv = build_filtered_list(
        scope="tablets",
        base_path="/tablets",
        query_args={
            "search": search,
            "period": period,
            "provenience": provenience,
            "genre": genre,
            "language": language,
            "has_ocr": "1" if has_ocr else "",
        },
        filter_dims=["period", "provenience", "genre", "language", "has_ocr"],
        page_obj=artifact_page,
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
    api = request.app.state.api

    tablet = api.get_artifact(p_number)
    if not tablet:
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
        # get_me and get_saved_items degrade gracefully — no try/except needed
        current_user = api.get_me(token) or None
        items = api.get_saved_items({"item_type": "artifact"}, token)
        for item in items:
            if item.get("item_id") == p_number:
                saved_item_id = item["id"]
                break

    # Debug: full data dump + tablet navigation list
    debug_json = None
    debug_tablets_json = None
    settings = get_settings()
    if settings.app_debug:
        debug_data = api.get_artifact_debug(p_number)
        if debug_data:
            debug_json = json.dumps(debug_data, default=str, ensure_ascii=False)
        else:
            logger.warning("Debug fetch empty for %s", p_number)
            debug_json = None

        try:
            debug_tablets_json = _DEBUG_TABLETS_PATH.read_text()
        except FileNotFoundError:
            debug_tablets_json = None

    # summarize_url: the API endpoint that generates/retrieves the AI artifact summary.
    # Passed as a data attribute so sidebar.js can fetch without constructing the URL in JS.
    summarize_url = f"{request.app.state.api.base_url}/artifacts/{p_number}/summary"

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "tablets/detail.html",
        {
            "tablet": tablet,
            "p_number": p_number,
            "back_url": back_url,
            "api_url": request.app.state.api.base_url,
            "summarize_url": summarize_url,
            "current_user": current_user,
            "saved_item_id": saved_item_id,
            "debug_json": debug_json,
            "debug_tablets_json": debug_tablets_json,
            "web_url": settings.web_url,
        },
    )
