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
    params: dict = {"page": page, "per_page": 24}
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

    # Pass active filters to filter-options for cross-filter counts
    filter_params: dict = {}
    if period:
        filter_params["period"] = period
    if provenience:
        filter_params["provenience"] = provenience
    if genre:
        filter_params["genre"] = genre
    if language:
        filter_params["language"] = language

    try:
        filter_options = api.get("/artifacts/filter-options", params=filter_params)
    except Exception:
        filter_options = {"period": [], "provenience": [], "genre": [], "language": []}

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
        "tablets/list.html",
        {
            "request": request,
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
    api = request.app.state.api

    try:
        tablet = api.get(f"/artifacts/{p_number}")
    except Exception:
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/tablets", status_code=302)

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
        "tablets/detail.html",
        {
            "request": request,
            "tablet": tablet,
            "api_url": request.app.state.api.base_url,
            "debug_json": debug_json,
            "debug_tablets_json": debug_tablets_json,
            "web_url": settings.web_url,
        },
    )
