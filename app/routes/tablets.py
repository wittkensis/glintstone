"""Tablet routes — list and detail."""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Request

from core.config import get_settings

_DEBUG_TABLETS_PATH = Path(__file__).resolve().parents[2] / "debug-tablets.json"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tablets")


@router.get("")
def tablet_list(
    request: Request,
    search: str = "",
    pipeline: str = "",
    period: str = "",
    provenience: str = "",
    genre: str = "",
    language: str = "",
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

    try:
        filter_options = api.get("/artifacts/filter-options")
    except Exception:
        filter_options = {"period": [], "provenience": [], "genre": [], "language": []}

    from app.main import templates

    # Active filters dict for template URL building
    filters = {}
    if search:
        filters["search"] = search
    if pipeline:
        filters["pipeline"] = pipeline
    if period:
        filters["period"] = period
    if provenience:
        filters["provenience"] = provenience
    if genre:
        filters["genre"] = genre
    if language:
        filters["language"] = language
    if has_ocr:
        filters["has_ocr"] = "1"

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
            "filters": filters,
            "filter_options": filter_options,
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
