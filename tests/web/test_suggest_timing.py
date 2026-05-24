"""Typeahead timing instrumentation and UX-contract tests.

These tests verify the suggest endpoint from the user's perspective:
- Response time is logged for every non-empty query
- The endpoint never raises — API failures surface as an empty drawer, not a 500
- Cache headers prevent stale results
- Scope filtering correctly gates what types are searched
- The HTML fragment is usable: rows have links, labels, and pipeline badges
- Edge cases: unicode queries, limit bounds, unknown scope
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _FakeAPI:
    def __init__(self, envelope=None):
        self.envelope = envelope or {"data": {"groups": []}, "summary": ""}
        self.calls: list[dict] = []
        self.base_url = "http://api.test"
        self.raise_on_call = False

    def get(self, path, params=None, token=None):
        if "saved-items" in path:
            return []
        if self.raise_on_call:
            raise ConnectionError("API unreachable")
        self.calls.append({"path": path, "params": params})
        return self.envelope

    def post(self, *a, **kw):
        return {}

    def close(self):
        pass


@pytest.fixture
def client(monkeypatch):
    from core import database

    monkeypatch.setattr(database, "init_pool", lambda *a, **kw: None)
    monkeypatch.setattr(database, "close_pool", lambda *a, **kw: None)

    from app import main as app_main
    from app.api_client import APIClient

    fake = _FakeAPI()

    monkeypatch.setattr(
        APIClient,
        "__init__",
        lambda self: (
            setattr(self, "base_url", fake.base_url) or setattr(self, "_client", None)
        ),
    )
    monkeypatch.setattr(
        APIClient, "get", lambda self, path, params=None: fake.get(path, params)
    )
    monkeypatch.setattr(APIClient, "post", lambda self, *a, **kw: {})
    monkeypatch.setattr(APIClient, "put", lambda self, *a, **kw: {})
    monkeypatch.setattr(APIClient, "delete", lambda self, *a, **kw: {})
    monkeypatch.setattr(APIClient, "close", lambda self: None)

    with TestClient(app_main.app, cookies={"session_token": "test-token"}) as c:
        c.app.state.api = fake
        c.fake = fake
        yield c


# ── Timing instrumentation ────────────────────────────────────────────────────


def test_suggest_logs_duration_for_non_empty_query(client, caplog):
    """Every non-empty suggest call must produce a duration_ms log entry."""
    with caplog.at_level(logging.INFO, logger="app.routes.search"):
        client.get("/_search/suggest?q=Nippur&scope=all")

    assert any("duration_ms=" in r.message for r in caplog.records)


def test_suggest_logs_scope_and_query(client, caplog):
    """Log line should include scope= and q= for debuggability."""
    with caplog.at_level(logging.INFO, logger="app.routes.search"):
        client.get("/_search/suggest?q=Lagash&scope=tablets")

    msg = next((r.message for r in caplog.records if "duration_ms=" in r.message), None)
    assert msg is not None
    assert "scope=tablets" in msg
    assert "Lagash" in msg


def test_suggest_does_not_log_for_empty_query(client, caplog):
    """Empty queries short-circuit before the API call — no duration log."""
    with caplog.at_level(logging.INFO, logger="app.routes.search"):
        client.get("/_search/suggest?q=&scope=all")

    assert not any("duration_ms=" in r.message for r in caplog.records)


# ── Resilience: API failure must not surface as 500 ──────────────────────────


def test_suggest_returns_empty_drawer_when_api_raises(client):
    """If the upstream API call fails, the drawer shows empty results — not an error."""
    client.fake.raise_on_call = True
    r = client.get("/_search/suggest?q=Gilgamesh&scope=all")
    # Must be 200, not 500 — the user sees "no results", not a crash
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_suggest_no_results_renders_gracefully(client):
    """Empty group list renders a 'No results' message, not a blank/broken page."""
    client.fake.envelope = {"data": {"groups": []}, "summary": ""}
    r = client.get("/_search/suggest?q=xyzzy_nosuch&scope=all")
    assert r.status_code == 200
    assert "No results" in r.text


# ── Cache headers ─────────────────────────────────────────────────────────────


def test_suggest_cache_control_prevents_stale_results(client):
    """Cache-Control header must forbid browser caching of search fragments."""
    r = client.get("/_search/suggest?q=king&scope=all")
    cc = r.headers.get("cache-control", "")
    assert "no-store" in cc


def test_suggest_empty_query_also_has_no_store(client):
    """204 responses must also carry no-store so the browser doesn't cache them."""
    r = client.get("/_search/suggest?q=&scope=all")
    assert r.status_code == 204
    cc = r.headers.get("cache-control", "")
    assert "no-store" in cc


# ── HTML fragment quality: what the user actually sees ───────────────────────


def test_suggest_result_rows_are_linked(client):
    """Each search row must be a clickable link — users need to navigate to results."""
    client.fake.envelope = {
        "data": {
            "groups": [
                {
                    "group_type": "tablets",
                    "items": [
                        {
                            "entity_id": "P123456",
                            "primary_label": "Old Babylonian tablet",
                            "secondary_label": "Nippur",
                            "p_number": "P123456",
                            "thumbnail_url": None,
                            "pipeline_completeness": 2,
                            "pipeline_stages": [1, 1, 0, 0, 0],
                            "score": 0.85,
                            "sources": ["cdli"],
                        }
                    ],
                    "total": 1,
                }
            ]
        },
        "summary": "",
    }
    r = client.get("/_search/suggest?q=babylon&scope=tablets")
    assert r.status_code == 200
    # Row must be a link (href present) — users must be able to click through
    assert "href=" in r.text
    assert "P123456" in r.text


def test_suggest_shows_primary_label(client):
    """Primary label (tablet designation, lemma, scholar name) must be visible."""
    client.fake.envelope = {
        "data": {
            "groups": [
                {
                    "group_type": "scholars",
                    "items": [
                        {
                            "entity_id": "s42",
                            "primary_label": "Niek Veldhuis",
                            "secondary_label": "UC Berkeley",
                            "p_number": None,
                            "thumbnail_url": None,
                            "pipeline_completeness": None,
                            "pipeline_stages": None,
                            "score": 0.9,
                            "sources": ["cdli"],
                        }
                    ],
                    "total": 1,
                }
            ]
        },
        "summary": "",
    }
    r = client.get("/_search/suggest?q=Veldhuis&scope=scholars")
    assert r.status_code == 200
    assert "Niek Veldhuis" in r.text


def test_suggest_pipeline_badge_present_for_tablet_results(client):
    """Tablet rows must carry pipeline completeness dots — scholars rely on these."""
    client.fake.envelope = {
        "data": {
            "groups": [
                {
                    "group_type": "tablets",
                    "items": [
                        {
                            "entity_id": "P654321",
                            "primary_label": "Ur III tablet",
                            "secondary_label": "Ur III",
                            "p_number": "P654321",
                            "thumbnail_url": None,
                            "pipeline_completeness": 5,
                            "pipeline_stages": [1, 1, 1, 1, 1],
                            "score": 0.95,
                            "sources": ["cdli"],
                        }
                    ],
                    "total": 1,
                }
            ]
        },
        "summary": "",
    }
    r = client.get("/_search/suggest?q=ur&scope=tablets")
    assert r.status_code == 200
    assert "pipeline-mini" in r.text


def test_suggest_see_all_link_shows_total_count(client):
    """When total > items returned, a 'See all N' link must appear for pagination."""
    client.fake.envelope = {
        "data": {
            "groups": [
                {
                    "group_type": "tablets",
                    "items": [
                        {
                            "entity_id": "P000001",
                            "primary_label": "Tablet 1",
                            "secondary_label": None,
                            "p_number": "P000001",
                            "thumbnail_url": None,
                            "pipeline_completeness": 0,
                            "pipeline_stages": [0, 0, 0, 0, 0],
                            "score": 0.7,
                            "sources": [],
                        }
                    ],
                    "total": 999,
                }
            ]
        },
        "summary": "",
    }
    r = client.get("/_search/suggest?q=tablet&scope=tablets")
    assert r.status_code == 200
    assert "999" in r.text


# ── Scope and type routing ─────────────────────────────────────────────────────


def test_suggest_dictionary_scope_sends_lemmas_signs_glosses(client):
    client.get("/_search/suggest?q=king&scope=dictionary")
    last = client.fake.calls[-1]
    assert sorted(last["params"]["types"]) == ["glosses", "lemmas", "signs"]


def test_suggest_collections_scope_sends_only_collections(client):
    client.get("/_search/suggest?q=nippur&scope=collections")
    last = client.fake.calls[-1]
    assert last["params"]["types"] == ["collections"]


def test_suggest_unknown_scope_falls_back_to_all_types(client):
    client.get("/_search/suggest?q=foo&scope=totally_unknown")
    last = client.fake.calls[-1]
    assert set(last["params"]["types"]) == {
        "tablets",
        "collections",
        "lemmas",
        "signs",
        "scholars",
    }


# ── Unicode and special character queries ─────────────────────────────────────


@pytest.mark.parametrize(
    "q",
    [
        "šarru",
        "Ṣilli-Adad",
        "lugal-àm",
        "𒀭𒂗𒍪",
        "héros",
        "Nūr-Adad",
    ],
)
def test_suggest_unicode_queries_return_200_or_204(client, q):
    """Unicode queries (cuneiform, accented Latin) must never crash the endpoint."""
    import urllib.parse

    r = client.get(f"/_search/suggest?q={urllib.parse.quote(q)}&scope=all")
    assert r.status_code in (200, 204)


def test_suggest_api_call_uses_hybrid_mode(client):
    """Typeahead must use hybrid search mode for best result quality."""
    client.get("/_search/suggest?q=Nippur&scope=all")
    last = client.fake.calls[-1]
    assert last["params"]["mode"] == "hybrid"
