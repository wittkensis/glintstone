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
        sort = "name" if level == "signs" else "frequency"

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


@router.get("/lemmas/{lemma_id}")
def lemma_detail(request: Request, lemma_id: int):
    api = request.app.state.api
    try:
        data = api.get(f"/dictionary/lemmas/{lemma_id}")
    except Exception:
        data = None
    if not data:
        return RedirectResponse(url="/dictionary", status_code=302)

    from app.main import templates

    return templates.TemplateResponse(
        request,
        "dictionary/lemma.html",
        {
            "lemma": data.get("lemma", {}),
            "senses": data.get("senses", []),
            "signs": data.get("signs", []),
            "tablet_count": data.get("tablet_count"),
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
