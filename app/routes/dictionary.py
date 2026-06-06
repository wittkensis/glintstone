"""Dictionary route — browse signs, lemmas, and glosses."""

from fastapi import APIRouter, Query, Request

from app.list_view import Page, build_filtered_list, active_filters_as_dicts

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

    try:
        data = api.get("/dictionary/browse", params=params)
    except Exception:
        data = {"items": [], "total": 0, "page": 1, "per_page": 50, "total_pages": 0}

    # Dictionary uses a separate filter-options endpoint (cross-filtered counts).
    # We inject those into the Page so the assembler can expose them to the template.
    filter_params: dict = {"level": level}
    if language:
        filter_params["language"] = language
    if pos:
        filter_params["pos"] = pos
    if source:
        filter_params["source"] = source
    if frequency:
        filter_params["frequency"] = frequency

    try:
        filter_options = api.get("/dictionary/filter-options", params=filter_params)
    except Exception:
        filter_options = {}

    # Build the label cache from filter_options so pill labels are human-readable
    # (e.g. language code "sux" → "Sumerian"). This shared cache avoids duplicating
    # the resolution logic in every route that has coded option values.
    label_cache: dict[tuple[str, str], str] = {}
    for dim_name in ("language", "pos", "source", "frequency"):
        for opt in filter_options.get(dim_name, []):
            label_cache[(dim_name, opt["val"])] = opt.get("label", opt["val"])

    # Inject filter_options into the page dict before wrapping so the assembler
    # passes them through to the template context via lv.filter_options.
    data_with_opts = dict(data)
    data_with_opts["filter_options"] = filter_options
    page_obj = Page.from_dict(data_with_opts, per_page=50)

    # level and sort must survive in remove-URLs — they're state, not filters.
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
        page_obj=page_obj,
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
            "filter_options": lv.filter_options,
            "active_filters": active_filters_as_dicts(lv),
            "api_url": request.app.state.api.base_url,
        },
    )
