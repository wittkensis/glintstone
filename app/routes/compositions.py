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
    limit: int = 100,
    offset: int = 0,
):
    api = request.app.state.api
    params: dict = {"limit": limit, "offset": offset}
    if search:
        params["q"] = search
    if sort:
        params["sort"] = sort

    try:
        data = api.get("/composites", params=params)
        composites = data.get("items", [])
        total = data.get("total", 0)
    except Exception:
        composites = []
        total = 0

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
    try:
        composite = api.get(f"/composites/{q_number}")
    except Exception:
        return RedirectResponse(url="/compositions", status_code=302)

    try:
        exemplars_data = api.get(f"/composites/{q_number}/exemplars")
        # API returns {q_number, exemplars: [...], count: N}
        exemplars = (
            exemplars_data.get("exemplars", [])
            if isinstance(exemplars_data, dict)
            else []
        )
        linked_count = len(exemplars)
    except Exception:
        exemplars = []
        linked_count = 0

    # Build filter option sets from exemplar data
    periods = sorted({e.get("period") for e in exemplars if e.get("period")})
    proveniences = sorted(
        {e.get("provenience") for e in exemplars if e.get("provenience")}
    )

    # Apply client-side filters
    filtered = exemplars
    if filter_period:
        filtered = [e for e in filtered if e.get("period") == filter_period]
    if filter_provenience:
        filtered = [e for e in filtered if e.get("provenience") == filter_provenience]

    # Build transmission history: group exemplars by period for the timeline
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

    for ex in exemplars:
        period = ex.get("period") or "Unknown period"
        if period not in timeline:
            timeline[period] = []
        timeline[period].append(ex)

    timeline_sorted = sorted(timeline.items(), key=lambda kv: _period_sort_key(kv[0]))

    # Count transparency: ORACC exemplar_count vs our linked count
    oracc_count = (
        composite.get("exemplar_count") if isinstance(composite, dict) else None
    )

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "compositions/detail.html",
        {
            "composite": composite if isinstance(composite, dict) else {},
            "exemplars": filtered,
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
