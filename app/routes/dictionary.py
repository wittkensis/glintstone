"""Dictionary route — browse signs, lemmas, and glosses with detail pages."""

from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse

from app.list_view import active_filters_as_dicts, build_filtered_list

router = APIRouter(prefix="/dictionary")


@router.get("")
def dictionary_index(
    request: Request,
    level: str = "lemmas",
    search: str = "",
    language: list[str] = Query(default=[]),
    pos: list[str] = Query(default=[]),
    source: list[str] = Query(default=[]),
    frequency: str = "",
    sort: str = "",
    page: int = 1,
):
    api = request.app.state.api

    # Normalize level
    if level not in ("signs", "lemmas", "glosses"):
        level = "lemmas"

    # Default sort per level
    if not sort:
        if level == "signs":
            sort = "name"
        elif level == "glosses":
            sort = "attestations"
        else:
            sort = "frequency"

    # Build API params
    params: dict = {"level": level, "page": page, "per_page": 50, "sort": sort}
    if search:
        params["search"] = search
    if language:
        params["language"] = language
    if pos:
        params["pos"] = pos
    if source:
        params["source"] = source
    if frequency:
        params["frequency"] = frequency

    dict_page = api.browse_dictionary(params)

    # Filter options (cross-filtered) — separate call, degrades to {}
    filter_params: dict = {"level": level}
    if language:
        filter_params["language"] = language
    if pos:
        filter_params["pos"] = pos
    if source:
        filter_params["source"] = source
    if frequency:
        filter_params["frequency"] = frequency

    filter_options = api.get_dictionary_filter_options(filter_params)

    # Build label cache from cross-filter options (coded val \u2192 human label)
    label_cache: dict[tuple[str, str], str] = {}
    for dim_name in ("language", "pos", "source", "frequency"):
        for opt in filter_options.get(dim_name, []):
            label_cache[(dim_name, opt["val"])] = opt.get("label", opt["val"])

    lv = build_filtered_list(
        scope="dictionary",
        base_path="/dictionary",
        query_args={
            "search": search,
            "language": language,
            "pos": pos,
            "source": source,
            "frequency": frequency,
        },
        filter_dims=["language", "pos", "source", "frequency"],
        page_obj=dict_page,
        label_cache=label_cache,
        preserve_params={"level": level, "sort": sort},
    )

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "dictionary/index.html",
        {
            "level": level,
            "items": lv.items,
            "total": lv.total,
            "page": lv.page,
            "total_pages": lv.total_pages,
            "search": search,
            "language": language,
            "pos": pos,
            "source": source,
            "frequency": frequency,
            "sort": sort,
            "filter_options": filter_options,
            "active_filters": active_filters_as_dicts(lv),
            "api_url": request.app.state.api.base_url,
        },
    )


@router.get("/search")
def dictionary_search(
    request: Request,
    q: str = "",
    search: str = "",
    level: str = "lemmas",
    language: list[str] = Query(default=[]),
    pos: list[str] = Query(default=[]),
    source: list[str] = Query(default=[]),
    frequency: str = "",
    sort: str = "",
):
    """Stable, shareable dictionary search/exploratory entry (#185, #284).

    The dictionary index at ``/dictionary`` is *already* the faceted exploratory
    surface — a search box, language/type/source/frequency facets (#163), level
    switcher, pagination, and a fully URL-encoded state that deep-links and the
    back button both respect. Rather than fork a second, divergent results page,
    this route is the canonical **entry point** for that surface: it accepts the
    ``/dictionary/search?q=…`` shape that the cmd+K drawer, external links, and
    the missing-/search expectation (#284) all reach for, normalises ``q`` →
    ``search``, and forwards (carrying every facet through) to the one index.

    One page, one source of truth — no second copy of the browse logic to drift.
    """
    # Accept either ?q= (the conventional search-page param) or ?search= (the
    # index's own param); q wins when both are present.
    term = (q or search).strip()

    params: list[tuple[str, str]] = []
    if level and level != "lemmas":
        params.append(("level", level))
    if term:
        params.append(("search", term))
    for v in language:
        params.append(("language", v))
    for v in pos:
        params.append(("pos", v))
    for v in source:
        params.append(("source", v))
    if frequency:
        params.append(("frequency", frequency))
    if sort:
        params.append(("sort", sort))

    from urllib.parse import urlencode

    target = "/dictionary"
    if params:
        target += "?" + urlencode(params)
    # 302 (not 301) so the canonical index can evolve its URL contract freely.
    return RedirectResponse(url=target, status_code=302)


@router.get("/lemmas/{lemma_id}")
def lemma_detail(request: Request, lemma_id: int, page: int = Query(1, ge=1)):
    api = request.app.state.api
    try:
        data = api.get(f"/dictionary/lemmas/{lemma_id}")
    except Exception:
        data = None
    if not data:
        return RedirectResponse(url="/dictionary", status_code=302)

    # Morphology sidebar — second, non-fatal call. The page must never 500
    # because the norm/form chain is unavailable; on any failure we render
    # the page with an empty sidebar (treated as the empty/unindexed state).
    try:
        norms_data = api.get(f"/dictionary/lemmas/{lemma_id}/norms")
        norms = (norms_data or {}).get("norms", [])
    except Exception:
        norms = []

    # Inline attestation table (#176) — the tablet lines where this lemma is
    # actually written, replacing the old count+jump card. Third, non-fatal
    # call: if the attestation endpoint is unavailable the page still renders
    # (the table falls back to the empty state rather than 500ing).
    try:
        attestations = api.get(
            f"/dictionary/lemmas/{lemma_id}/attestations",
            params={"page": page, "per_page": 20},
        )
    except Exception:
        attestations = None

    # Per-period attestation timeline (#201) — the chronological spread of the
    # word's usage across canonical periods, on a proportional BCE axis.
    # Fourth, non-fatal call: on any failure the timeline section renders its
    # empty state rather than 500ing the page.
    try:
        attestation_periods = api.get(
            f"/dictionary/lemmas/{lemma_id}/attestation-periods"
        )
    except Exception:
        attestation_periods = None

    # Compositions using this lemma (#529) — top compositions by attestation
    # line count. Non-fatal: degrades to empty list if unavailable.
    try:
        compositions_data = api.get(f"/dictionary/lemmas/{lemma_id}/compositions")
        lemma_compositions = (compositions_data or {}).get("items", [])
    except Exception:
        lemma_compositions = []

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "dictionary/lemma.html",
        {
            "lemma": data.get("lemma", {}),
            "senses": data.get("senses", []),
            "signs": data.get("signs", []),
            "norms": norms,
            "attestations": attestations or {},
            "attestation_periods": attestation_periods or {},
            "api_url": request.app.state.api.base_url,
            "lemma_compositions": lemma_compositions,
        },
    )


@router.get("/senses/{sense_id}")
def sense_detail(request: Request, sense_id: int):
    """Detail page for a single dictionary sense (#184) — one meaning of a
    lemma, with its translations, source, and the lemma's other senses. On any
    API failure or a missing sense we redirect to the dictionary index rather
    than 500-ing (mirrors the lemma/sign routes).
    """
    api = request.app.state.api
    try:
        data = api.get(f"/dictionary/senses/{sense_id}")
    except Exception:
        data = None
    if not data:
        return RedirectResponse(url="/dictionary", status_code=302)

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "dictionary/sense.html",
        {
            "sense": data.get("sense", {}),
            "lemma": data.get("lemma", {}),
            "sibling_senses": data.get("sibling_senses", []),
            "api_url": request.app.state.api.base_url,
        },
    )


@router.get("/signs/{sign_id}")
def sign_detail(request: Request, sign_id: int):
    api = request.app.state.api
    try:
        data = api.get(f"/dictionary/signs/{sign_id}")
    except Exception:
        data = None
    if not data:
        return RedirectResponse(url="/dictionary?level=signs", status_code=302)

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "dictionary/sign.html",
        {
            "sign": data.get("sign", {}),
            "lemmas": data.get("lemmas", []),
            "api_url": request.app.state.api.base_url,
        },
    )


@router.get("/glosses/{guide_word:path}")
def gloss_detail(request: Request, guide_word: str, pos: str = ""):
    """Detail page for a *gloss group* (#184) — all lemmas that share one guide
    word (e.g. every dictionary entry meaning "king"), a cross-lemma view of a
    single meaning across the corpus. Backed by the existing
    /dictionary/glosses/{guide_word} API. ``:path`` lets guide words containing
    slashes resolve. On failure or an unknown gloss we redirect to the glosses
    browse rather than 500-ing.
    """
    api = request.app.state.api
    params = {"pos": pos} if pos else None
    try:
        data = api.get(f"/dictionary/glosses/{guide_word}", params=params)
    except Exception:
        data = None
    if not data:
        return RedirectResponse(url="/dictionary?level=glosses", status_code=302)

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "dictionary/gloss.html",
        {
            "guide_word": data.get("guide_word", guide_word),
            "pos_label": data.get("pos_label", ""),
            "lemmas": data.get("lemmas", []),
            "total_attestations": data.get("total_attestations", 0),
            "api_url": request.app.state.api.base_url,
        },
    )
