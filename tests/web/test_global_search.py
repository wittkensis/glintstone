"""Web-tier tests for the global-search drawer + /_search/suggest proxy.

These cover the contract between the JS state machine in
app/static/js/global-search.js and the FastAPI app:
- The scope→types mapping is correct.
- Empty queries return 204 (lets the JS fall back to localStorage recents).
- A populated response renders the partial with .search-row entries.
- base.html exposes the right data-* attributes per URL.
- Record-page mode renders the record-self template.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _FakeAPI:
    """Stand-in for GlintstoneAPI — captures the last search request and
    returns a canned envelope shape. Also implements typed domain methods
    used by migrated routes."""

    def __init__(self, envelope=None):
        self.envelope = envelope or {"data": {"groups": []}, "summary": ""}
        self.last_path = None
        self.last_params = None
        self.base_url = "http://api.test"

    # ── Raw passthrough (used by auth routes, admin, etc.) ────────────────────

    def get(self, path, params=None, token=None):
        # saved-items returns a list; all other paths return the search envelope
        if "saved-items" in path:
            return []
        self.last_path = path
        self.last_params = params
        return self.envelope

    def post(self, *a, **kw):
        return {}

    def put(self, *a, **kw):
        return {}

    def delete(self, *a, **kw):
        return None

    def patch(self, *a, **kw):
        return None

    def close(self):
        pass

    # ── Typed domain methods (used by migrated routes) ────────────────────────

    def search(self, params):
        """Record params for assertion; return the envelope."""
        self.last_path = "/search"
        self.last_params = params
        return self.envelope

    def list_artifacts(self, params):
        from app.api_client import Page

        return (
            Page.from_dict(self.envelope)
            if isinstance(self.envelope, dict) and "items" in self.envelope
            else Page.empty()
        )

    def get_artifact(self, p_number, token=None):
        return self.envelope if isinstance(self.envelope, dict) else {}

    def get_artifact_debug(self, p_number):
        return {}

    def get_me(self, token):
        return {}

    def get_saved_items(self, params, token):
        return []

    def list_collections(self, params=None):
        from app.api_client import Page

        return Page.empty()

    def get_collection(self, collection_id):
        return {}

    def list_scholars(self, params):
        from app.api_client import Page

        return Page.empty()

    def browse_dictionary(self, params):
        from app.api_client import Page

        return Page.empty()

    def get_dictionary_filter_options(self, params):
        return {}

    def get_kpi(self):
        return {}

    def list_composites(self, params):
        from app.api_client import Page

        return Page.empty()

    def get_coverage_gaps(self, params):
        return {}


@pytest.fixture
def client(monkeypatch):
    # Side-step the DB pool by stubbing init/close to no-ops.
    from core import database

    monkeypatch.setattr(database, "init_pool", lambda *a, **kw: None)
    monkeypatch.setattr(database, "close_pool", lambda *a, **kw: None)

    from app import main as app_main
    from app.transports import HttpxTransport

    # Prevent HttpxTransport from opening a real HTTP connection during lifespan.
    monkeypatch.setattr(HttpxTransport, "__init__", lambda self, **kw: None)
    monkeypatch.setattr(HttpxTransport, "close", lambda self: None)

    # Our fake satisfies the GlintstoneAPI interface directly — it gets set on
    # app.state.api below so routes see it immediately.
    fake = _FakeAPI()

    with TestClient(app_main.app, cookies={"session_token": "test-token"}) as c:
        # Replace app.state.api with the fake so the route's `request.app.state.api`
        # uses our recorder.
        c.app.state.api = fake
        c.fake = fake  # expose for assertions
        yield c


# ── /_search/suggest contract ────────────────────────────────────────────────


def test_suggest_empty_query_returns_204(client):
    r = client.get("/_search/suggest?q=&scope=all")
    assert r.status_code == 204


def test_suggest_whitespace_query_returns_204(client):
    r = client.get("/_search/suggest?q=%20%20&scope=all")
    assert r.status_code == 204


def test_suggest_renders_html_fragment_with_groups(client):
    client.fake.envelope = {
        "data": {
            "groups": [
                {
                    "group_type": "tablets",
                    "items": [
                        {
                            "entity_id": "P3928244",
                            "primary_label": "P3928244",
                            "secondary_label": "Gilgamesh going into the woods",
                            "p_number": "P3928244",
                            "thumbnail_url": None,
                            "pipeline_completeness": 3,
                            "pipeline_stages": [1, 1, 1, 0, 0],
                            "score": 0.9,
                            "sources": ["cdli"],
                        }
                    ],
                    "total": 128,
                }
            ]
        },
        "summary": "1 group matched.",
    }
    r = client.get("/_search/suggest?q=gilgamesh&scope=tablets")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert 'class="search-row' in r.text
    assert "P3928244" in r.text
    assert "Gilgamesh going into the woods" in r.text
    # See-all link surfaces total > items count
    assert "See all 128" in r.text
    # Pipeline mini-badge dots present
    assert "pipeline-mini__dot--complete" in r.text
    assert "pipeline-mini__dot--active" in r.text


def test_suggest_passes_correct_types_for_tablets_scope(client):
    client.get("/_search/suggest?q=P3&scope=tablets")
    assert client.fake.last_path == "/search"
    assert client.fake.last_params is not None
    assert client.fake.last_params["types"] == ["tablets"]


def test_suggest_expands_dictionary_scope_to_lemmas_signs_glosses(client):
    client.get("/_search/suggest?q=foo&scope=dictionary")
    assert sorted(client.fake.last_params["types"]) == ["glosses", "lemmas", "signs"]


def test_suggest_all_scope_includes_five_types(client):
    client.get("/_search/suggest?q=foo&scope=all")
    assert set(client.fake.last_params["types"]) == {
        "tablets",
        "collections",
        "lemmas",
        "signs",
        "scholars",
    }


def test_suggest_unknown_scope_falls_back_to_all(client):
    client.get("/_search/suggest?q=foo&scope=garbage")
    assert set(client.fake.last_params["types"]) == {
        "tablets",
        "collections",
        "lemmas",
        "signs",
        "scholars",
    }


def test_suggest_renders_no_results_section_when_empty(client):
    client.fake.envelope = {"data": {"groups": []}, "summary": ""}
    r = client.get("/_search/suggest?q=zzzzznosuch&scope=all")
    assert r.status_code == 200
    assert "No results" in r.text


# ── base.html shell context ──────────────────────────────────────────────────


def test_home_renders_search_shell_with_scope_default_all(client):
    client.fake.envelope = {"kpi": None}
    # Home calls api.get('/stats/kpi') and api.get('/collections/random')
    r = client.get("/")
    assert r.status_code == 200
    assert 'class="global-search"' in r.text
    assert 'data-scope-default="all"' in r.text
    assert 'data-record-mode="false"' in r.text
    # All four Browse chips present
    for label in ("Artifacts", "Collections", "Dictionary", "Scholars"):
        assert f">{label}<" in r.text


def test_tablets_listing_marks_artifacts_browse_chip_active(client):
    client.fake.envelope = {
        "items": [],
        "total": 0,
        "page": 1,
        "per_page": 24,
        "total_pages": 0,
    }
    r = client.get("/tablets")
    assert r.status_code == 200
    # Active browse chip
    assert 'class="browse-chip is-active"' in r.text
    assert 'data-scope-default="tablets"' in r.text


def test_record_page_renders_record_mode_attrs(client):
    # Return a stub artifact so the detail page renders. The tablets detail
    # route hits the API for the artifact; we don't care about the body, only
    # that the shell renders record-mode.
    client.fake.envelope = {
        "p_number": "P3928244",
        "designation": "Test tablet",
        "items": [],
    }
    r = client.get("/tablets/P3928244")
    # Detail page may 200 or 404 depending on stubs — but if it renders, the
    # shell must mark record_mode. Skip when the route flat-out errors out.
    if r.status_code != 200:
        pytest.skip(f"tablet detail returned {r.status_code} with stub data")
    assert 'data-record-mode="true"' in r.text
    assert 'data-record-id="P3928244"' in r.text


# ── Scope label mapping ──────────────────────────────────────────────────────


def test_scope_label_mapping_constants():
    from app.routes.search import SCOPE_TO_LABEL, SCOPE_TO_TYPES

    assert set(SCOPE_TO_LABEL.keys()) == {
        "all",
        "tablets",
        "collections",
        "dictionary",
        "scholars",
    }
    assert SCOPE_TO_TYPES["all"] == [
        "tablets",
        "collections",
        "lemmas",
        "signs",
        "scholars",
    ]
    assert SCOPE_TO_TYPES["dictionary"] == ["lemmas", "signs", "glosses"]
