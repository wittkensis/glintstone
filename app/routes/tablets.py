"""Tablet routes — list and detail."""

import concurrent.futures
import json
import logging
import math
from pathlib import Path
from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse

from app.corpus_map import VIEW_H as MAP_VIEW_H
from app.corpus_map import VIEW_W as MAP_VIEW_W
from app.corpus_map import build_pins, build_single_pin
from app.list_view import active_filters_as_dicts, build_filtered_list
from core.config import get_settings

_DEBUG_TABLETS_PATH = Path(__file__).resolve().parents[2] / "debug-tablets.json"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tablets")


def _atlas_filter_params(
    search: str,
    pipeline: str,
    period: list[str],
    provenience: list[str],
    genre: list[str],
    language: list[str],
    has_ocr: str,
) -> dict:
    """Build the filter params (sans pagination) shared by the timeline and
    by-site aggregate calls — exactly the predicates the grid uses, so a brush
    re-filters the corpus the same way the checkboxes do."""
    p: dict = {}
    if search:
        p["search"] = search
    if pipeline:
        p["pipeline"] = pipeline
    if period:
        p["period"] = period
    if provenience:
        p["provenience"] = provenience
    if genre:
        p["genre"] = genre
    if language:
        p["language"] = language
    if has_ocr:
        p["has_ocr"] = "true"
    return p


def _timeline_axis(rows: list[dict]) -> list[dict]:
    """Decorate per-period rows with log-scaled bar geometry + proportional BCE
    position so the Timeline view renders honestly without JS (Tufte: log scale
    keeps the 111k Ur III skew from drowning the small periods).

    Adds to each row:
      - ``bar_width``: percent width of the count bar (log10-scaled).
      - ``bar_left``: percent offset on the shared 3000→0 BCE axis (from
        date_start_bce); 0 when the period has no canonical date.
    The axis spans 3000 BCE (left) to 0 (right). Counts are scaled so the
    largest period reads ~100%% and a single tablet still shows a visible stub.
    """
    AXIS_MAX_BCE = 3000.0
    if not rows:
        return []
    max_count = max((r.get("count") or 0) for r in rows) or 1
    log_max = math.log10(max_count + 1) or 1.0
    out: list[dict] = []
    for r in rows:
        count = r.get("count") or 0
        # log-scale the bar; floor at 4% so tiny periods stay clickable/visible
        width = max(4.0, (math.log10(count + 1) / log_max) * 100.0)
        # Anchor the count-bar at the date the period *starts* on the shared
        # BCE axis, then clamp its width so it never runs past the right edge of
        # the track (left + width <= 100). This keeps the bar both positioned in
        # time (where on the 3000→0 BCE axis) and sized by count (log), matching
        # the Tufte coverage-matrix encoding in the spec without overflow.
        start = r.get("date_start_bce")
        if start is not None:
            bce = abs(start)
            # Axis runs 3000 BCE (0%) → 0 BCE (100%). Periods older than 3000
            # BCE pin to the left edge.
            left = max(0.0, min(96.0, (1 - bce / AXIS_MAX_BCE) * 100.0))
        else:
            left = 0.0
        width = min(width, 100.0 - left)
        out.append(
            {
                **r,
                "bar_width": round(width, 1),
                "bar_left": round(left, 1),
            }
        )
    return out


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
    view: str = "grid",
):
    api = request.app.state.api
    # Grid / timeline (#320) + map (#197, gated on #319's geocoded coords). The
    # map plots each geolocated find-spot as a proportional symbol and lets a
    # click set ?provenience= — the same linked filter as the find-spots list.
    # Anything unknown falls back to the grid so a stale URL never lands blank.
    if view not in ("grid", "timeline", "map"):
        view = "grid"
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

    # Corpus-Atlas aggregates (#320): per-period counts (timeline) + ranked
    # find-spots (geography lens), both over the SAME active filter as the grid.
    # Fetched on every load so the view-switcher flips instantly client-side and
    # the no-JS fallback server-renders whichever view the URL asked for.
    atlas_params = _atlas_filter_params(
        search, pipeline, period, provenience, genre, language, has_ocr
    )

    # #115 — these API round trips are independent of one another, so fire them
    # concurrently instead of sequentially. The page artifact list, the timeline
    # aggregate, the by-site aggregate (and, on the map view, the site coords) all
    # hit the API over HTTP; running them in parallel collapses the page-load
    # latency from the SUM of the calls to the MAX. httpx.Client is thread-safe
    # for concurrent requests, and every api.* method here already degrades to an
    # empty/well-formed result on failure, so a slow or failing branch can never
    # 500 the page — same contract as before, just overlapped. Mirrors the
    # ThreadPoolExecutor pattern in core/agent/search_engine.py.
    want_coords = view == "map"
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        page_future = executor.submit(api.list_artifacts, params)
        timeline_future = executor.submit(api.get_artifacts_timeline, atlas_params)
        site_future = executor.submit(
            api.get_artifacts_by_site, {**atlas_params, "limit": 12}
        )
        coords_future = executor.submit(api.get_site_coords) if want_coords else None

        artifact_page = page_future.result()
        timeline_rows = _timeline_axis(timeline_future.result())
        site_rows = site_future.result()

    # Map view (#197): geolocated find-spots as proportional symbols. The pins
    # show the full geographic distribution of the corpus (a navigation surface,
    # not a filtered slice) — clicking one sets ?provenience= via the SAME linked
    # filter as the find-spots list. Built only when the map view is requested so
    # grid/timeline loads don't pay for the coords round trip. `not_geocoded` is
    # the count of geolocated-site rows the schematic box couldn't place (≈0 by
    # design) — uncertain-provenance tablets are reported separately.
    map_pins: list = []
    map_uncertain = 0
    if coords_future is not None:
        coords = coords_future.result()
        map_pins = build_pins(coords.get("sites", []))
        map_uncertain = (coords.get("uncertain") or {}).get("tablet_count", 0)

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
            "view": view,
            "timeline_rows": timeline_rows,
            "site_rows": site_rows,
            "map_pins": map_pins,
            "map_uncertain": map_uncertain,
            "map_view_w": MAP_VIEW_W,
            "map_view_h": MAP_VIEW_H,
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

    # Recognized Signs (#535): ML sign-reading predictions (Akkademia). Degrades
    # to an empty result; the detail template only renders the section when there
    # are signs, so a tablet without predictions shows nothing extra.
    sign_recognitions = api.get_sign_recognitions(p_number)

    # Find-spot mini-map (#199): pin this single tablet's excavation site, if it
    # has coordinates. The find-spot is where the tablet was *excavated*
    # (gs-expert-assyriology) — the provenience string ("Umma (mod. …)") is
    # normalized to the canonical ancient_name and matched against the geocoded
    # sites. No coords (e.g. uncertain provenance, or an ungeocoded site like
    # Nineveh in production) → no map; the Provenience field still shows the name.
    map_pin = None
    raw_prov = (tablet.get("provenience") or "").split("(mod.")[0].strip()
    if raw_prov and raw_prov.lower() not in ("uncertain", "unknown"):
        coords = api.get_site_coords()
        for s in coords.get("sites", []):
            if (s.get("ancient_name") or "").lower() == raw_prov.lower() and s.get(
                "latitude"
            ) is not None:
                # Single fixed-size pin — count is meaningless for one tablet.
                map_pin = build_single_pin(s)
                break

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
            "sign_recognitions": sign_recognitions,
            "current_user": current_user,
            "saved_item_id": saved_item_id,
            "debug_json": debug_json,
            "debug_tablets_json": debug_tablets_json,
            "web_url": settings.web_url,
            "map_pin": map_pin,
            "map_view_w": MAP_VIEW_W,
            "map_view_h": MAP_VIEW_H,
        },
    )
