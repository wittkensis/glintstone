"""ListView assembler — shared pattern for filtered, paginated list pages.

All four list routes (tablets, dictionary, scholars, collections) share the same
"active filter pill + remove-URL" pattern. This module centralises it so bugs
are fixed in one place and new list pages inherit it for free.
"""

from dataclasses import dataclass, field
from urllib.parse import quote


@dataclass
class Page:
    """Thin wrapper around a raw API paginated response dict.

    Routes call `api.get(...)` which returns a plain dict. Wrapping it here
    gives the assembler a typed contract and keeps the routes simple.
    """

    items: list[dict]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    filter_options: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict, *, per_page: int = 24) -> "Page":
        """Construct a Page from a raw API response dict."""
        total = data.get("total", 0)
        page = data.get("page", 1)
        total_pages = data.get("total_pages", 0)
        has_next = page < total_pages if total_pages else False
        return cls(
            items=data.get("items", []),
            total=total,
            page=page,
            per_page=data.get("per_page", per_page),
            total_pages=total_pages,
            has_next=has_next,
            filter_options=data.get("filter_options") or {},
        )


@dataclass
class ActiveFilter:
    key: str
    label: str  # human-readable text for the pill
    remove_url: str  # URL with this filter removed


@dataclass
class ListView:
    items: list[dict]
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    active_filters: list[ActiveFilter]
    filter_options: dict
    scope: str  # 'tablets' | 'dictionary' | 'scholars' | 'collections'


# Hard-coded flag labels that don't correspond to a human-readable value.
_PILL_LABELS: dict[str, str] = {
    "has_ocr": "Has ML/OCR",
}


def _pill_label(
    key: str,
    val: str,
    label_cache: dict[tuple[str, str], str] | None = None,
) -> str:
    """Resolve a human-readable label for a filter pill.

    Resolution order:
    1. Hard-coded flag labels (e.g. has_ocr)
    2. Shared label cache populated by the route from filter_options
    3. The raw value string as a fallback
    Special case: 'search' is wrapped in curly quotes.
    """
    if key in _PILL_LABELS:
        return _PILL_LABELS[key]
    if key == "search":
        return f"“{val}”"
    if label_cache is not None:
        cached = label_cache.get((key, val))
        if cached is not None:
            return cached
    return val


def build_filtered_list(
    scope: str,
    base_path: str,
    query_args: dict,
    filter_dims: list[str],
    page_obj: Page,
    label_cache: dict[tuple[str, str], str] | None = None,
    preserve_params: dict[str, str] | None = None,
) -> ListView:
    """Build a ListView from a Page response and current query args.

    Args:
        scope: 'tablets' | 'dictionary' | 'scholars' | 'collections'
        base_path: e.g. '/tablets' — base URL for building remove-links
        query_args: dict of {dimension: value_or_list} from the request
        filter_dims: list of filter dimension keys (e.g. ['period', 'genre'])
        page_obj: a Page dataclass
        label_cache: optional {(dim, val): label} map for human-readable pills.
            Callers populate it from filter_options when the API provides labels.
        preserve_params: optional {key: value} params that must always appear in
            remove-URLs (e.g. {'level': 'lemmas', 'sort': 'frequency'} for the
            dictionary route). These are never treated as removable filters.
    """
    # Collect the (key, value) pairs that are currently active as filters.
    # Search comes first so its pill appears at the left of the pill row.
    all_params: list[tuple[str, str]] = []

    search = query_args.get("search", "")
    if search:
        all_params.append(("search", search))

    for dim in filter_dims:
        val = query_args.get(dim)
        if not val:
            continue
        if isinstance(val, list):
            for v in val:
                if v:
                    all_params.append((dim, v))
        else:
            all_params.append((dim, val))

    # Params that are always preserved in remove-URLs but are not pills.
    # Example: pipeline in tablets, level+sort in dictionary.
    _preserve: dict[str, str] = preserve_params or {}

    # Build a pill for each active filter; its remove_url omits that one entry.
    active_filters: list[ActiveFilter] = []
    for i, (key, val) in enumerate(all_params):
        remaining = [
            f"{k}={quote(v, safe='')}" for j, (k, v) in enumerate(all_params) if j != i
        ]
        # Append preserved params (level, sort, pipeline…) that aren't pills
        for pk, pv in _preserve.items():
            if pv:
                remaining.append(f"{pk}={quote(pv, safe='')}")
        qs = "&".join(remaining)
        remove_url = f"{base_path}?{qs}" if qs else base_path
        active_filters.append(
            ActiveFilter(
                key=key,
                label=_pill_label(key, val, label_cache),
                remove_url=remove_url,
            )
        )

    return ListView(
        items=page_obj.items,
        page=page_obj.page,
        per_page=page_obj.per_page,
        total=page_obj.total,
        total_pages=page_obj.total_pages,
        has_next=page_obj.has_next,
        active_filters=active_filters,
        filter_options=page_obj.filter_options,
        scope=scope,
    )


def active_filters_as_dicts(lv: ListView) -> list[dict]:
    """Convert ListView.active_filters to the dict format templates expect.

    Templates use {{ f.dimension }}, {{ f.label }}, {{ f.remove_url }}.
    """
    return [
        {"dimension": f.key, "label": f.label, "remove_url": f.remove_url}
        for f in lv.active_filters
    ]
