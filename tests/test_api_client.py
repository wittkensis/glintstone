"""Tests for GlintstoneAPI using InMemoryTransport.

These tests verify the degrade-to-empty contract: every domain method returns a
safe empty value on failure, and correctly maps fixture data to typed results.
"""

from app.api_client import GlintstoneAPI, Page
from app.transports import InMemoryTransport


def make_api(fixtures: dict | None = None) -> GlintstoneAPI:
    return GlintstoneAPI(InMemoryTransport(fixtures or {}))


# ── Page.from_dict ────────────────────────────────────────────────────────────


def test_page_from_dict_maps_fields():
    data = {
        "items": [{"id": 1}],
        "total": 42,
        "page": 3,
        "per_page": 10,
        "total_pages": 5,
        "has_next": True,
        "filter_options": {"period": ["Ur III"]},
    }
    page = Page.from_dict(data)
    assert page.items == [{"id": 1}]
    assert page.total == 42
    assert page.page == 3
    assert page.per_page == 10
    assert page.total_pages == 5
    assert page.has_next is True
    assert page.filter_options == {"period": ["Ur III"]}


def test_page_empty_defaults():
    page = Page.empty()
    assert page.items == []
    assert page.total == 0
    assert page.page == 1
    assert page.total_pages == 0
    assert page.has_next is False


# ── Artifacts ─────────────────────────────────────────────────────────────────


def test_list_artifacts_empty_on_missing_fixture():
    api = make_api({})
    page = api.list_artifacts({})
    assert isinstance(page, Page)
    assert page.items == []
    assert page.total == 0


def test_list_artifacts_returns_page():
    api = make_api(
        {
            "/artifacts": {
                "items": [{"p_number": "P000001"}],
                "total": 1,
                "page": 1,
                "per_page": 24,
                "total_pages": 1,
            }
        }
    )
    page = api.list_artifacts({})
    assert len(page.items) == 1
    assert page.items[0]["p_number"] == "P000001"
    assert page.total == 1


def test_get_artifact_returns_empty_on_failure():
    api = make_api({})
    assert api.get_artifact("P000001") == {}


def test_get_artifact_returns_fixture():
    api = make_api({"/artifacts/P000001": {"p_number": "P000001", "title": "Test"}})
    result = api.get_artifact("P000001")
    assert result["p_number"] == "P000001"


def test_get_artifact_debug_returns_empty_on_failure():
    api = make_api({})
    assert api.get_artifact_debug("P000001") == {}


# ── Auth / User ───────────────────────────────────────────────────────────────


def test_get_me_returns_empty_on_failure():
    api = make_api({})
    assert api.get_me("bad-token") == {}


def test_get_saved_items_returns_empty_list_on_failure():
    api = make_api({})
    result = api.get_saved_items({}, "token")
    assert result == []


def test_get_saved_items_returns_list_from_fixture():
    api = make_api({"/users/me/saved-items": [{"id": "abc", "item_id": "P000001"}]})
    result = api.get_saved_items({}, "token")
    assert len(result) == 1
    assert result[0]["item_id"] == "P000001"


# ── Dictionary ────────────────────────────────────────────────────────────────


def test_browse_dictionary_empty_on_failure():
    api = make_api({})
    page = api.browse_dictionary({})
    assert isinstance(page, Page)
    assert page.items == []


def test_browse_dictionary_returns_page():
    api = make_api(
        {
            "/dictionary/browse": {
                "items": [{"id": 1, "headword": "lugal"}],
                "total": 1,
                "page": 1,
                "per_page": 50,
                "total_pages": 1,
            }
        }
    )
    page = api.browse_dictionary({"level": "lemmas"})
    assert len(page.items) == 1
    assert page.items[0]["headword"] == "lugal"


def test_get_dictionary_filter_options_empty_on_failure():
    api = make_api({})
    result = api.get_dictionary_filter_options({})
    assert result == {}


# ── Scholars ──────────────────────────────────────────────────────────────────


def test_list_scholars_empty_on_failure():
    api = make_api({})
    page = api.list_scholars({})
    assert isinstance(page, Page)
    assert page.items == []


def test_list_scholars_returns_page():
    api = make_api(
        {
            "/scholars": {
                "items": [{"id": 1, "name": "Adam Falkenstein"}],
                "total": 1,
                "page": 1,
                "per_page": 24,
                "total_pages": 1,
            }
        }
    )
    page = api.list_scholars({})
    assert page.items[0]["name"] == "Adam Falkenstein"


# ── Collections ───────────────────────────────────────────────────────────────


def test_list_collections_empty_on_failure():
    api = make_api({})
    page = api.list_collections()
    assert isinstance(page, Page)
    assert page.items == []


def test_get_collection_returns_empty_on_failure():
    api = make_api({})
    assert api.get_collection(999) == {}


# ── Search ────────────────────────────────────────────────────────────────────


def test_search_returns_empty_dict_on_failure():
    api = make_api({})
    result = api.search({"q": "lugal"})
    assert result == {}


def test_search_returns_fixture():
    envelope = {"data": {"groups": [{"type": "tablets", "hits": []}]}}
    api = make_api({"/search": envelope})
    result = api.search({"q": "lugal"})
    assert "data" in result


# ── Transport protocol check ──────────────────────────────────────────────────


def test_in_memory_transport_satisfies_protocol():
    from app.transports import Transport

    t = InMemoryTransport({})
    assert isinstance(t, Transport)
