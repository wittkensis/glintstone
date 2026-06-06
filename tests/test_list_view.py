"""Unit tests for the ListView assembler (app/list_view.py).

These tests are purely in-memory — no HTTP, no database, no app startup.
"""

from app.list_view import (
    Page,
    build_filtered_list,
    active_filters_as_dicts,
    _pill_label,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_page(**kwargs) -> Page:
    defaults = dict(
        items=[],
        total=0,
        page=1,
        per_page=24,
        total_pages=0,
        has_next=False,
        filter_options={},
    )
    defaults.update(kwargs)
    return Page(**defaults)


# ---------------------------------------------------------------------------
# Page.from_dict
# ---------------------------------------------------------------------------


def test_page_from_dict_basic():
    data = {
        "items": [{"p_number": "P000001"}],
        "total": 1,
        "page": 1,
        "per_page": 24,
        "total_pages": 1,
    }
    p = Page.from_dict(data)
    assert p.items == [{"p_number": "P000001"}]
    assert p.total == 1
    assert p.has_next is False


def test_page_from_dict_has_next():
    data = {"items": [], "total": 50, "page": 1, "per_page": 24, "total_pages": 3}
    p = Page.from_dict(data)
    assert p.has_next is True


def test_page_from_dict_last_page_no_next():
    data = {"items": [], "total": 50, "page": 3, "per_page": 24, "total_pages": 3}
    p = Page.from_dict(data)
    assert p.has_next is False


def test_page_from_dict_filter_options_preserved():
    data = {
        "items": [],
        "total": 0,
        "page": 1,
        "per_page": 24,
        "total_pages": 0,
        "filter_options": {"period": [{"val": "Ur III", "count": 42}]},
    }
    p = Page.from_dict(data)
    assert p.filter_options["period"][0]["val"] == "Ur III"


def test_page_from_dict_empty_response():
    p = Page.from_dict({})
    assert p.items == []
    assert p.total == 0
    assert p.has_next is False


# ---------------------------------------------------------------------------
# _pill_label
# ---------------------------------------------------------------------------


def test_pill_label_has_ocr_flag():
    assert _pill_label("has_ocr", "1") == "Has ML/OCR"


def test_pill_label_search_quoted():
    assert _pill_label("search", "royal") == "“royal”"


def test_pill_label_from_cache():
    cache = {("language", "sux"): "Sumerian"}
    assert _pill_label("language", "sux", label_cache=cache) == "Sumerian"


def test_pill_label_raw_fallback():
    assert _pill_label("period", "Ur III") == "Ur III"


def test_pill_label_cache_miss_falls_back_to_raw():
    cache = {("language", "akk"): "Akkadian"}
    assert _pill_label("language", "sux", label_cache=cache) == "sux"


# ---------------------------------------------------------------------------
# build_filtered_list — basic cases
# ---------------------------------------------------------------------------


def test_empty_query_no_filters():
    page = make_page(items=[{"p_number": "P000001"}], total=1, total_pages=1)
    lv = build_filtered_list("tablets", "/tablets", {}, ["period", "genre"], page)
    assert lv.active_filters == []
    assert lv.items == [{"p_number": "P000001"}]
    assert lv.total == 1
    assert lv.scope == "tablets"


def test_single_filter_pill_string():
    page = make_page(total=5)
    lv = build_filtered_list(
        "tablets",
        "/tablets",
        {"period": "Ur III"},
        ["period", "genre"],
        page,
    )
    assert len(lv.active_filters) == 1
    assert lv.active_filters[0].key == "period"
    assert lv.active_filters[0].label == "Ur III"
    assert lv.active_filters[0].remove_url == "/tablets"


def test_single_filter_pill_list():
    page = make_page(total=5)
    lv = build_filtered_list(
        "tablets",
        "/tablets",
        {"period": ["Ur III"], "genre": []},
        ["period", "genre"],
        page,
    )
    assert len(lv.active_filters) == 1
    assert lv.active_filters[0].key == "period"
    assert lv.active_filters[0].label == "Ur III"
    assert lv.active_filters[0].remove_url == "/tablets"


def test_two_filters_remove_url_cross_links():
    """Removing one pill should leave the other in the URL."""
    page = make_page(total=3)
    lv = build_filtered_list(
        "tablets",
        "/tablets",
        {"period": ["Ur III"], "genre": ["administrative"]},
        ["period", "genre"],
        page,
    )
    assert len(lv.active_filters) == 2
    # Removing period pill → genre should stay
    period_pill = lv.active_filters[0]
    assert period_pill.key == "period"
    assert "genre=administrative" in period_pill.remove_url
    assert "period" not in period_pill.remove_url
    # Removing genre pill → period should stay
    # quote() encodes space as %20 (not +); both are valid percent-encoding
    genre_pill = lv.active_filters[1]
    assert genre_pill.key == "genre"
    assert "period=Ur%20III" in genre_pill.remove_url
    assert "genre" not in genre_pill.remove_url


def test_search_pill_comes_first():
    page = make_page(total=2)
    lv = build_filtered_list(
        "tablets",
        "/tablets",
        {"search": "royal", "period": ["Ur III"]},
        ["period"],
        page,
    )
    assert lv.active_filters[0].key == "search"
    assert lv.active_filters[1].key == "period"


def test_search_pill_quoted_label():
    page = make_page()
    lv = build_filtered_list("tablets", "/tablets", {"search": "royal"}, [], page)
    assert lv.active_filters[0].label == "“royal”"


def test_search_pill_remove_url_is_base():
    page = make_page()
    lv = build_filtered_list("tablets", "/tablets", {"search": "royal"}, [], page)
    assert lv.active_filters[0].remove_url == "/tablets"


def test_has_ocr_flag_pill_label():
    page = make_page()
    lv = build_filtered_list(
        "tablets",
        "/tablets",
        {"has_ocr": "1"},
        ["has_ocr"],
        page,
    )
    assert lv.active_filters[0].label == "Has ML/OCR"


# ---------------------------------------------------------------------------
# preserve_params
# ---------------------------------------------------------------------------


def test_preserve_params_appear_in_remove_url():
    """pipeline= must survive in all remove-URLs even though it's not a pill."""
    page = make_page(total=3)
    lv = build_filtered_list(
        "tablets",
        "/tablets",
        {"period": ["Ur III"]},
        ["period"],
        page,
        preserve_params={"pipeline": "ocr"},
    )
    assert len(lv.active_filters) == 1
    assert "pipeline=ocr" in lv.active_filters[0].remove_url


def test_preserve_params_not_a_pill():
    """Preserved params must NOT appear as filter pills themselves."""
    page = make_page(total=3)
    lv = build_filtered_list(
        "tablets",
        "/tablets",
        {"period": ["Ur III"], "pipeline": "ocr"},
        ["period"],  # pipeline is NOT in filter_dims
        page,
        preserve_params={"pipeline": "ocr"},
    )
    assert len(lv.active_filters) == 1
    assert lv.active_filters[0].key == "period"


def test_preserve_params_level_and_sort():
    """Dictionary route: level + sort must appear in all remove-URLs."""
    page = make_page(total=10)
    lv = build_filtered_list(
        "dictionary",
        "/dictionary",
        {"search": "lugal", "language": ["sux"]},
        ["language"],
        page,
        preserve_params={"level": "lemmas", "sort": "frequency"},
    )
    for f in lv.active_filters:
        assert "level=lemmas" in f.remove_url
        assert "sort=frequency" in f.remove_url


# ---------------------------------------------------------------------------
# label_cache
# ---------------------------------------------------------------------------


def test_label_cache_resolves_coded_values():
    cache = {("language", "sux"): "Sumerian", ("language", "akk"): "Akkadian"}
    page = make_page(total=5)
    lv = build_filtered_list(
        "dictionary",
        "/dictionary",
        {"language": ["sux"]},
        ["language"],
        page,
        label_cache=cache,
    )
    assert lv.active_filters[0].label == "Sumerian"


# ---------------------------------------------------------------------------
# scope
# ---------------------------------------------------------------------------


def test_scope_preserved_tablets():
    page = make_page()
    lv = build_filtered_list("tablets", "/tablets", {}, [], page)
    assert lv.scope == "tablets"


def test_scope_preserved_dictionary():
    page = make_page()
    lv = build_filtered_list("dictionary", "/dictionary", {}, ["language"], page)
    assert lv.scope == "dictionary"


def test_scope_preserved_scholars():
    page = make_page()
    lv = build_filtered_list("scholars", "/scholars", {}, [], page)
    assert lv.scope == "scholars"


def test_scope_preserved_collections():
    page = make_page()
    lv = build_filtered_list("collections", "/collections", {}, [], page)
    assert lv.scope == "collections"


# ---------------------------------------------------------------------------
# active_filters_as_dicts
# ---------------------------------------------------------------------------


def test_active_filters_as_dicts_format():
    """Templates expect dicts with 'dimension', 'label', 'remove_url' keys."""
    page = make_page(total=1)
    lv = build_filtered_list(
        "tablets", "/tablets", {"period": ["Ur III"]}, ["period"], page
    )
    result = active_filters_as_dicts(lv)
    assert len(result) == 1
    assert result[0] == {
        "dimension": "period",
        "label": "Ur III",
        "remove_url": "/tablets",
    }


def test_active_filters_as_dicts_empty():
    page = make_page()
    lv = build_filtered_list("tablets", "/tablets", {}, ["period"], page)
    assert active_filters_as_dicts(lv) == []


# ---------------------------------------------------------------------------
# Multi-value same dimension
# ---------------------------------------------------------------------------


def test_multi_value_same_dim():
    """Two values for the same dimension should produce two separate pills."""
    page = make_page(total=8)
    lv = build_filtered_list(
        "tablets",
        "/tablets",
        {"language": ["akk", "sux"]},
        ["language"],
        page,
    )
    assert len(lv.active_filters) == 2
    keys = [f.key for f in lv.active_filters]
    assert keys == ["language", "language"]
    labels = [f.label for f in lv.active_filters]
    assert "akk" in labels
    assert "sux" in labels
