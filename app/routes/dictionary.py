"""Dictionary route — browse signs, lemmas, and meanings."""

from urllib.parse import quote

from fastapi import APIRouter, Query, Request

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
    if level not in ("signs", "lemmas", "meanings"):
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

    # Filter options (cross-filtered)
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

    # Build active filter pills with remove URLs
    all_params: list[tuple[str, str]] = []
    if search:
        all_params.append(("search", search))
    for lang in language:
        all_params.append(("language", lang))
    for p in pos:
        all_params.append(("pos", p))
    for s in source:
        all_params.append(("source", s))
    if frequency:
        all_params.append(("frequency", frequency))

    # Find filter option labels for pills
    _label_cache: dict[tuple[str, str]] = {}
    for dim_name in ("language", "pos", "source", "frequency"):
        opts = filter_options.get(dim_name, [])
        for opt in opts:
            _label_cache[(dim_name, opt["val"])] = opt.get("label", opt["val"])

    def _pill_label(key: str, val: str) -> str:
        if key == "search":
            return f"\u201c{val}\u201d"
        return _label_cache.get((key, val), val)

    active_filters: list[dict] = []
    for i, (key, val) in enumerate(all_params):
        remaining = [
            f"{k}={quote(v, safe='')}" for j, (k, v) in enumerate(all_params) if j != i
        ]
        # Always preserve level and sort
        remaining.append(f"level={level}")
        if sort:
            remaining.append(f"sort={sort}")
        qs = "&".join(remaining)
        remove_url = f"/dictionary?{qs}" if qs else "/dictionary"
        active_filters.append(
            {
                "dimension": key,
                "label": _pill_label(key, val),
                "remove_url": remove_url,
            }
        )

    from app.main import templates

    return templates.TemplateResponse(
        "dictionary/index.html",
        {
            "request": request,
            "level": level,
            "items": data.get("items", []),
            "total": data.get("total", 0),
            "page": data.get("page", 1),
            "total_pages": data.get("total_pages", 0),
            "search": search,
            "language": language,
            "pos": pos,
            "source": source,
            "frequency": frequency,
            "sort": sort,
            "filter_options": filter_options,
            "active_filters": active_filters,
            "api_url": request.app.state.api.base_url,
        },
    )
