"""Compositions routes — first-class browse and detail for canonical texts."""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.corpus_map import VIEW_H as MAP_VIEW_H
from app.corpus_map import VIEW_W as MAP_VIEW_W
from app.corpus_map import build_pins

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


# Exemplars rendered per page in the detail table. A heavy composition
# (Q005026 = 3,635 witnesses) used to render every row inline, producing a
# ~6.4 MB HTML document. The table is now server-side paginated to this many
# rows; the SVG timeline + find-spots map still receive the full set (they are
# per-witness visualizations and need every dot), but those carry only a few
# fields per row, not full table markup.
EXEMPLARS_PER_PAGE = 50


@router.get("/{q_number}")
def composition_detail(
    request: Request,
    q_number: str,
    filter_period: str = "",
    filter_provenience: str = "",
    ex_page: int = 1,
):
    api = request.app.state.api
    composite = api.get_composite(q_number)
    if not composite:
        return RedirectResponse(url="/compositions", status_code=302)

    # Auth-aware: the #169 scholar-correction widget is shown only to signed-in
    # scholars (it writes a correction attributed to them). get_me degrades to
    # None for anonymous visitors.
    current_user = None
    token = request.cookies.get("session_token")
    if token:
        current_user = api.get_me(token) or None

    # get_composite returns {"composite": {...}, "exemplars": [...]}
    # Handle both flat and nested response shapes gracefully
    if isinstance(composite, dict) and "composite" in composite:
        composite_meta = composite.get("composite") or {}
        all_exemplars = composite.get("exemplars", [])
        atf_preview = composite.get("atf_preview")
        related = composite.get("related") or []
    else:
        composite_meta = composite if isinstance(composite, dict) else {}
        exemplars_data = api.get_composite_exemplars(q_number)
        all_exemplars = exemplars_data.get("exemplars", [])
        atf_preview = None
        related = []

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

    # Derive translation-coverage label per exemplar from pipeline_status.
    # semantic_complete is the canonical "has a translation" signal (pipeline
    # stage 4 = at least one non-empty translation). It is written 1.0/0.0
    # today (effectively binary), so in practice only Translated/Untranslated
    # appear; the "partial" band is future-proofing for fractional values.
    #   >= 0.99            -> Translated   (green)
    #   > 0 and < 0.99     -> Partial      (amber)
    #   0 / NULL / no row  -> Untranslated (neutral gray)
    def _coverage(e: dict) -> str:
        raw = e.get("semantic_complete")
        try:
            score = float(raw) if raw is not None else 0.0
        except (TypeError, ValueError):
            score = 1.0 if e.get("has_translation") else 0.0
        if score >= 0.99:
            return "translated"
        if score > 0:
            return "partial"
        return "untranslated"

    filtered = [{**e, "coverage": _coverage(e)} for e in filtered]

    # Server-side pagination of the exemplars *table* (the heavy part of the
    # page). The timeline + map below still see all_exemplars; only the rendered
    # table is sliced. filtered_total is the count after the period/provenience
    # filters but before paging, so the pager and the "N exemplars" label match
    # the filtered view the scholar is looking at.
    import math as _math

    filtered_total = len(filtered)
    exemplar_pages = max(1, _math.ceil(filtered_total / EXEMPLARS_PER_PAGE))
    # Clamp the requested page into range so a hand-typed ?ex_page never 500s or
    # renders an empty table for an in-range result set.
    ex_page = max(1, min(ex_page, exemplar_pages))
    _start = (ex_page - 1) * EXEMPLARS_PER_PAGE
    exemplars_page = filtered[_start : _start + EXEMPLARS_PER_PAGE]

    # #404 Concept A — witness-switcher + extent column.
    # `extent_max` = the most readable ATF lines any single witness holds; the
    # extent bar in the exemplars table is each witness's count / this max, so
    # "which witness is most complete?" reads straight off the table. Computed
    # over ALL exemplars (not the filtered view) so the bar's scale stays stable
    # while a scholar filters by site/period.
    extent_max = max((e.get("atf_line_count") or 0 for e in all_exemplars), default=0)

    # Witnesses readable in the switcher: those carrying readable ATF, best-
    # preserved first (strongest comparanda surface first — spec default). The
    # representative witness (matches the pre-loaded preview) is starred and
    # pre-selected. A single readable witness renders one non-interactive chip.
    rep_p = (atf_preview or {}).get("p_number")
    witnesses = sorted(
        (
            {**e, "coverage": _coverage(e)}
            for e in all_exemplars
            if (e.get("atf_line_count") or 0) > 0
        ),
        key=lambda e: (-(e.get("atf_line_count") or 0), e.get("p_number") or ""),
    )

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

    # Composition find-spots map (#198): where this text's witnesses were
    # excavated. We count each exemplar's provenience, then intersect with the
    # geocoded sites (GET /proveniences/coords) so the circle area reflects how
    # many of THIS composition's tablets came from each site — the geographic
    # companion to the transmission timeline. Witnesses whose provenience is
    # uncertain or has no coordinates simply don't pin (reported in the caption).
    map_pins: list = []
    map_no_coords = 0
    from collections import Counter

    def _canon_prov(raw: str) -> str:
        # Exemplar provenience is the display string ("Uruk (mod. Warka)"); the
        # coords API keys on the canonical ancient_name ("Uruk"). Strip the
        # "(mod. …)" suffix so the two line up.
        return (raw.split("(mod.")[0] if raw else "").strip()

    prov_counts: Counter = Counter(
        _canon_prov(e.get("provenience"))
        for e in all_exemplars
        if e.get("provenience")
        and _canon_prov(e.get("provenience")).lower()
        not in ("uncertain", "unknown", "")
    )
    if prov_counts:
        coords = api.get_site_coords()
        by_name = {
            (s.get("ancient_name") or "").lower(): s for s in coords.get("sites", [])
        }
        scoped_sites = []
        placed_total = 0
        for name, cnt in prov_counts.items():
            site = by_name.get(name.lower())
            if site and site.get("latitude") is not None:
                scoped_sites.append({**site, "tablet_count": cnt})
                placed_total += cnt
        map_pins = build_pins(scoped_sites)
        # Witnesses with a real site name that we still couldn't place on the map
        # (no coordinates for that site) — surfaced honestly in the caption.
        map_no_coords = sum(prov_counts.values()) - placed_total

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
            "exemplars": exemplars_page,
            "exemplars_total": filtered_total,
            "ex_page": ex_page,
            "exemplar_pages": exemplar_pages,
            "exemplars_per_page": EXEMPLARS_PER_PAGE,
            "atf_preview": atf_preview,
            "related": related,
            "current_user": current_user,
            "witnesses": witnesses,
            "extent_max": extent_max,
            "rep_p": rep_p,
            "timeline_exemplars": timeline_exemplars,
            "linked_count": linked_count,
            "oracc_count": oracc_count,
            "timeline": timeline_sorted,
            "periods": periods,
            "proveniences": proveniences,
            "filter_period": filter_period,
            "filter_provenience": filter_provenience,
            "api_url": request.app.state.api.base_url,
            "map_pins": map_pins,
            "map_no_coords": map_no_coords,
            "map_view_w": MAP_VIEW_W,
            "map_view_h": MAP_VIEW_H,
        },
    )
