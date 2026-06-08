"""Compositions routes — first-class browse and detail for canonical texts."""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/compositions")


@router.get("")
def compositions_list(
    request: Request,
    search: str = "",
    lang: str = "",
    genre: str = "",
    period: str = "",
    sort: str = "exemplar_count",
    limit: int = 500,
    offset: int = 0,
):
    api = request.app.state.api
    params: dict = {"limit": limit, "offset": offset}
    if search:
        params["q"] = search
    if sort:
        params["sort"] = sort

    page = api.list_composites(params)
    composites = page.items
    total = page.total

    # Build filter sets from result data for the facets
    genres = sorted({c.get("genre") for c in composites if c.get("genre")})
    languages = sorted({c.get("language") for c in composites if c.get("language")})
    periods = sorted({c.get("period") for c in composites if c.get("period")})

    # Client-side filter (lang/genre/period filters applied post-fetch since
    # the /composites API doesn't yet support these params)
    if lang:
        composites = [
            c for c in composites if (c.get("language") or "").lower() == lang.lower()
        ]
    if genre:
        composites = [
            c for c in composites if (c.get("genre") or "").lower() == genre.lower()
        ]
    if period:
        composites = [
            c for c in composites if (c.get("period") or "").lower() == period.lower()
        ]

    # Build Canon: top-N compositions by exemplar count (sorted desc already)
    # We sort by exemplar_count desc — composites come back sorted by exemplar_count
    # per the sort param above.
    sorted_by_count = sorted(
        composites, key=lambda c: c.get("exemplar_count") or 0, reverse=True
    )
    canon_top = sorted_by_count[:20]
    canon_extended = sorted_by_count[:50]
    canon_max = canon_top[0].get("exemplar_count") or 1 if canon_top else 1

    # Build genre summary for genre tiles
    genre_counts: dict[str, int] = {}
    for c in composites:
        g = c.get("genre")
        if g:
            genre_counts[g] = genre_counts.get(g, 0) + 1
    genre_tiles = sorted(genre_counts.items(), key=lambda kv: kv[1], reverse=True)

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "compositions/index.html",
        {
            "composites": composites,
            "total": total,
            "search": search,
            "lang": lang,
            "genre": genre,
            "period": period,
            "genres": genres,
            "languages": languages,
            "periods": periods,
            "canon_top": canon_top,
            "canon_extended": canon_extended,
            "canon_max": canon_max,
            "genre_tiles": genre_tiles,
            "api_url": request.app.state.api.base_url,
        },
    )


@router.get("/{q_number}")
def composition_detail(
    request: Request,
    q_number: str,
    filter_period: str = "",
    filter_provenience: str = "",
):
    api = request.app.state.api
    composite = api.get_composite(q_number)
    if not composite:
        return RedirectResponse(url="/compositions", status_code=302)

    # get_composite returns {"composite": {...}, "exemplars": [...]}
    # Handle both flat and nested response shapes gracefully
    if isinstance(composite, dict) and "composite" in composite:
        composite_meta = composite.get("composite") or {}
        all_exemplars = composite.get("exemplars", [])
    else:
        composite_meta = composite if isinstance(composite, dict) else {}
        exemplars_data = api.get_composite_exemplars(q_number)
        all_exemplars = exemplars_data.get("exemplars", [])

    linked_count = len(all_exemplars)

    # Build filter option sets from exemplar data
    periods = sorted({e.get("period") for e in all_exemplars if e.get("period")})
    proveniences = sorted(
        {e.get("provenience") for e in all_exemplars if e.get("provenience")}
    )

    # Apply client-side filters for exemplar table
    filtered = all_exemplars
    if filter_period:
        filtered = [e for e in filtered if e.get("period") == filter_period]
    if filter_provenience:
        filtered = [e for e in filtered if e.get("provenience") == filter_provenience]

    # Build transmission history: group exemplars by period for the old row-based
    # timeline (kept for fallback; SVG timeline uses raw exemplars client-side)
    timeline: dict[str, list[dict]] = {}
    _PERIOD_ORDER = [
        "Early Dynastic",
        "Sargonic",
        "Ur III",
        "Old Babylonian",
        "Old Assyrian",
        "Middle Babylonian",
        "Middle Assyrian",
        "Middle Hittite",
        "Neo-Assyrian",
        "Neo-Babylonian",
        "Achaemenid",
        "Hellenistic",
        "Seleucid",
        "Parthian",
    ]

    def _period_sort_key(p: str) -> int:
        for i, label in enumerate(_PERIOD_ORDER):
            if label.lower() in p.lower():
                return i
        return 99

    for ex in all_exemplars:
        period = ex.get("period") or "Unknown period"
        if period not in timeline:
            timeline[period] = []
        timeline[period].append(ex)

    timeline_sorted = sorted(timeline.items(), key=lambda kv: _period_sort_key(kv[0]))

    # Count transparency: ORACC exemplar_count vs our linked count
    oracc_count = composite_meta.get("exemplar_count") if composite_meta else None

    # Build exemplar list for the SVG timeline (all exemplars, with pipeline_status)
    # pipeline_status may be present as a field; default to None if absent
    timeline_exemplars = [
        {
            "p_number": e.get("p_number") or e.get("id") or "",
            "period": e.get("period") or "",
            "pipeline_status": e.get("pipeline_status") or "",
            "designation": e.get("designation") or "",
            "provenience": e.get("provenience") or "",
            "museum": e.get("museum") or e.get("museum_no") or "",
        }
        for e in all_exemplars
        if (e.get("p_number") or e.get("id"))
    ]

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "compositions/detail.html",
        {
            "composite": composite_meta,
            "exemplars": filtered,
            "timeline_exemplars": timeline_exemplars,
            "linked_count": linked_count,
            "oracc_count": oracc_count,
            "timeline": timeline_sorted,
            "periods": periods,
            "proveniences": proveniences,
            "filter_period": filter_period,
            "filter_provenience": filter_provenience,
            "api_url": request.app.state.api.base_url,
        },
    )
