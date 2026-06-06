"""Tablet routes — list and detail."""

import json
import logging
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse

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

    filter_options = artifact_page.filter_options or {
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
            return f"“{val}”"
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
            "tablets": artifact_page.items,
            "total": artifact_page.total,
            "page": artifact_page.page,
            "total_pages": artifact_page.total_pages,
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
    api = request.app.state.api

    tablet = api.get_artifact(p_number)
    if not tablet:
        return RedirectResponse(url="/tablets", status_code=302)

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
