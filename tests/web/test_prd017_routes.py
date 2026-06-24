"""#114 — unit coverage for the PRD-017 web page routes (no live DB).

Audit finding 3b: integration tests can't reach the VPS Postgres from CI, so the
PRD-017 pages — compositions, dictionary, scholars, and the dashboard/home — had
no automated guard. A regression in any of these routes (a renamed API-client
method, a template context key drop, a 500 on an empty envelope) would ship
unnoticed.

These tests render each route through the real app + real GlintstoneAPI client,
with the HTTP transport replaced by an in-memory fixture map. The transport is
the seam that would normally hit the API (and through it, Postgres) — stubbing it
gives us true unit coverage of the route → client → template path with zero DB.

Scope note: per the chores-batch-2 split, the /tablets-list and provenience
routes are owned by concurrent PRs and are intentionally NOT covered here.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ── Fixtures shaped like the API's JSON envelopes ──────────────────────────────

_COMPOSITE = {
    "q_number": "Q000001",
    "designation": "Gilgamesh",
    "language": "Akkadian",
    "genre": "literary",
    "period": "Old Babylonian",
    "exemplar_count": 42,
}

_COMPOSITES_PAGE = {
    "items": [_COMPOSITE],
    "total": 1,
    "page": 1,
    "per_page": 50,
    "total_pages": 1,
}

_KPI = {
    "top_periods": [{"label": "Ur III", "count": 10}],
    "top_genres": [{"label": "literary", "count": 8}],
    "top_languages": [{"label": "Sumerian", "count": 12}],
}

_DICTIONARY_PAGE = {
    "items": [
        {"lemma_id": 1, "lemma": "lugal", "guide_word": "king", "attestations": 99}
    ],
    "total": 1,
    "page": 1,
    "per_page": 50,
    "total_pages": 1,
}

_SCHOLARS_PAGE = {"items": [], "total": 7, "page": 1, "per_page": 1, "total_pages": 7}


class _FixtureTransport:
    """Maps API paths to canned JSON. Anything unmapped returns an empty dict,
    which the GlintstoneAPI client degrades to an empty Page / {} envelope."""

    def __init__(self):
        self._fixtures = {
            "/composites": _COMPOSITES_PAGE,
            "/dictionary": _DICTIONARY_PAGE,
            "/scholars": _SCHOLARS_PAGE,
            "/kpi": _KPI,
            "/coverage-gaps": {"items": []},
            "/auth/me": {},
            "/users/me/saved-items": [],
            "/periods": {"items": []},
        }

    def get(self, path, params=None, token=None):
        # Exact match first, then prefix match for nested resource paths.
        if path in self._fixtures:
            return self._fixtures[path]
        for key, val in self._fixtures.items():
            if path.startswith(key):
                return val
        return {}

    def post(self, path, json=None, token=None):
        return {}

    def put(self, path, json=None, token=None):
        return {}

    def patch(self, path, json=None, token=None):
        return None

    def delete(self, path, token=None):
        return None

    def close(self):
        pass


@pytest.fixture
def client(monkeypatch):
    from core import database

    monkeypatch.setattr(database, "init_pool", lambda *a, **kw: None)
    monkeypatch.setattr(database, "close_pool", lambda *a, **kw: None)

    from app import main as app_main
    from app.api_client import GlintstoneAPI
    from app.transports import HttpxTransport

    monkeypatch.setattr(HttpxTransport, "__init__", lambda self, **kw: None)
    monkeypatch.setattr(HttpxTransport, "close", lambda self: None)

    fake_api = GlintstoneAPI(_FixtureTransport())
    with TestClient(app_main.app, cookies={"session_token": "test-token"}) as c:
        c.app.state.api = fake_api
        yield c


# ── Dashboard / home ───────────────────────────────────────────────────────────


def test_homepage_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    # Canon section is fed by list_composites — the designation should appear.
    assert "Gilgamesh" in r.text


def test_homepage_survives_empty_kpi(client):
    """A missing KPI envelope must not 500 the dashboard."""
    client.app.state.api._t._fixtures["/kpi"] = {}
    r = client.get("/")
    assert r.status_code == 200


# ── Compositions ───────────────────────────────────────────────────────────────


def test_compositions_list_renders(client):
    r = client.get("/compositions")
    assert r.status_code == 200
    assert "Gilgamesh" in r.text


def test_compositions_list_with_filters(client):
    """Client-side lang/genre/period filters must not error."""
    r = client.get("/compositions?lang=Akkadian&genre=literary")
    assert r.status_code == 200


def test_compositions_empty_envelope(client):
    """An empty /composites envelope renders an empty page, not a 500."""
    client.app.state.api._t._fixtures["/composites"] = {"items": [], "total": 0}
    r = client.get("/compositions")
    assert r.status_code == 200


# ── Dictionary ─────────────────────────────────────────────────────────────────


def test_dictionary_index_renders(client):
    r = client.get("/dictionary")
    assert r.status_code == 200


def test_dictionary_invalid_level_defaults(client):
    """An unknown ?level= is coerced to 'lemmas' rather than 500-ing."""
    r = client.get("/dictionary?level=bogus")
    assert r.status_code == 200


# ── Scholars ───────────────────────────────────────────────────────────────────


def test_scholars_list_renders(client):
    r = client.get("/scholars")
    assert r.status_code == 200
