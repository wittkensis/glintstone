"""#515 — unit coverage for the PRD-017 *API-tier* routes (no live DB).

Audit finding 3b (extended): integration tests can't reach the VPS Postgres from
CI. The companion ``test_prd017_routes.py`` already guards the PRD-017 *web* page
routes (``app/``) by stubbing the outbound httpx transport. But those web pages
call the API tier (``api/routes/*``), and the API tier itself — the compositions,
dictionary, scholars, and dashboard/stats endpoints — had NO automated guard that
runs without a live Postgres. A regression in one of these handlers (a dropped
envelope key, a 500 on an empty result, a lost 404 on a missing record, a mangled
pagination calculation) would ship unnoticed because CI can't reach the DB to
exercise them.

These tests mount the REAL FastAPI app and exercise each API route through the
real handler code. The DB is removed at two seams:

  1. ``app.dependency_overrides[get_db]`` yields a scripted fake connection
     instead of a pooled psycopg connection. Routes that run raw SQL directly
     on the connection cursor (the /scholars index, facets, and detail) read
     their rows from a queue of canned results on that fake cursor.

  2. Repository classes used by the composites / dictionary / stats routes are
     monkeypatched so their query methods return canned envelopes. The fake
     connection is still injected (the route constructs ``Repo(conn)``), but no
     SQL is ever executed against it.

Because ``get_db`` is overridden and the request carries no ``Authorization``
header, the auth middleware short-circuits to an anonymous request without ever
opening a real connection — so the whole suite runs with zero Postgres.

Scope: the four PRD-017 surfaces named in #515 — compositions (``/composites``),
dictionary (``/dictionary``), scholars (``/scholars``), and the dashboard/home
data endpoints (``/stats/kpi``, ``/stats/coverage-gaps``). Detail-page 404 paths
are covered because they are the most common silent regression.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ── Scripted fake DB connection ────────────────────────────────────────────────


class _FakeCursor:
    """A cursor whose ``fetchone`` / ``fetchall`` pop from a queue of canned
    results, in the order the route issues its ``execute`` calls.

    Only the surface the PRD-017 routes actually use is implemented: ``execute``
    (records the call, discards the SQL), ``fetchone`` / ``fetchall`` (pop the
    next queued result), and the context-manager protocol (``with conn.cursor()
    as cur``). ``execute`` returns the cursor so ``.fetchone()`` can be chained.
    """

    def __init__(self, results):
        self._results = list(results)
        self.executed: list[tuple] = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return self

    def _next(self):
        if not self._results:
            raise AssertionError(
                "FakeCursor exhausted: the route issued more fetches than the "
                "test queued results for. Add another entry to `results`."
            )
        return self._results.pop(0)

    def fetchone(self):
        return self._next()

    def fetchall(self):
        return self._next()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeConnection:
    """Stands in for a pooled psycopg connection. Hands out a single scripted
    ``_FakeCursor`` seeded with the queued results. A route that opens the cursor
    more than once (``with conn.cursor()`` twice) keeps reading the same queue,
    which matches how these handlers thread state across cursor blocks."""

    def __init__(self, results=None):
        self._cursor = _FakeCursor(results or [])

    def cursor(self):
        return self._cursor


def _make_client(monkeypatch, *, results=None):
    """Build a TestClient over the real API app with the DB fully stubbed.

    ``results`` is the queue of ``fetchone`` / ``fetchall`` returns for routes
    that run raw SQL (scholars). Repository-backed routes ignore it and are
    monkeypatched per-test instead.
    """
    from core import database

    # Never let importing / lifespan touch a real pool.
    monkeypatch.setattr(database, "init_pool", lambda *a, **kw: None)
    monkeypatch.setattr(database, "close_pool", lambda *a, **kw: None)

    from api import main as api_main
    from core.database import get_db

    fake_conn = _FakeConnection(results=results)
    api_main.app.dependency_overrides[get_db] = lambda: fake_conn

    client = TestClient(api_main.app)
    client._fake_conn = fake_conn  # exposed for assertions if a test wants it
    return client


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    """The API app is a module-global singleton, so the get_db override set by
    ``_make_client`` must be cleared after each test — otherwise it would leak
    into any later real-DB test that imported the same app object."""
    yield
    try:
        from api import main as api_main

        api_main.app.dependency_overrides.clear()
    except Exception:
        pass


# ── Canned envelopes shaped like the repositories return ───────────────────────

_COMPOSITE = {
    "q_number": "Q000001",
    "designation": "Gilgamesh",
    "language": "Akkadian",
    "genre": "literary",
    "period": "Old Babylonian",
    "exemplar_count": 42,
}

_LEMMA_PAGE = {
    "items": [
        {"lemma_id": 1, "lemma": "lugal", "guide_word": "king", "attestations": 99}
    ],
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


# ── Compositions (repo-backed) ─────────────────────────────────────────────────


def test_composites_list_returns_envelope(monkeypatch):
    """GET /composites returns the {items,total,limit,offset} envelope with the
    repository's rows — no filters means the find_all path."""
    from api.repositories.composite_repo import CompositeRepository

    monkeypatch.setattr(
        CompositeRepository, "find_all", lambda self, limit, offset: [_COMPOSITE]
    )
    monkeypatch.setattr(CompositeRepository, "get_total_count", lambda self: 1)

    client = _make_client(monkeypatch)
    r = client.get("/composites")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["designation"] == "Gilgamesh"
    assert body["limit"] == 100 and body["offset"] == 0


def test_composites_list_with_filters_uses_search(monkeypatch):
    """Any filter param routes through repo.search, not find_all."""
    from api.repositories.composite_repo import CompositeRepository

    calls = {"search": 0, "find_all": 0}

    def _search(self, **kw):
        calls["search"] += 1
        return [_COMPOSITE]

    def _find_all(self, limit, offset):
        calls["find_all"] += 1
        return []

    monkeypatch.setattr(CompositeRepository, "search", _search)
    monkeypatch.setattr(CompositeRepository, "find_all", _find_all)
    monkeypatch.setattr(CompositeRepository, "get_total_count", lambda self: 1)

    client = _make_client(monkeypatch)
    r = client.get("/composites?language=Akkadian&genre=literary")
    assert r.status_code == 200
    assert calls["search"] == 1 and calls["find_all"] == 0


def test_composites_list_empty(monkeypatch):
    """An empty corpus renders total=0 with no rows, not a 500."""
    from api.repositories.composite_repo import CompositeRepository

    monkeypatch.setattr(CompositeRepository, "find_all", lambda self, limit, offset: [])
    monkeypatch.setattr(CompositeRepository, "get_total_count", lambda self: 0)

    client = _make_client(monkeypatch)
    r = client.get("/composites")
    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0, "limit": 100, "offset": 0}


def test_composite_detail_ok(monkeypatch):
    """GET /composites/{q} assembles composite + exemplars + atf + related."""
    from api.repositories.composite_repo import CompositeRepository

    monkeypatch.setattr(
        CompositeRepository, "find_by_q_number", lambda self, q: _COMPOSITE
    )
    monkeypatch.setattr(CompositeRepository, "get_exemplars", lambda self, q: [])
    monkeypatch.setattr(
        CompositeRepository, "get_representative_atf_preview", lambda self, q: None
    )
    monkeypatch.setattr(
        CompositeRepository, "get_related_composites", lambda self, q: []
    )

    client = _make_client(monkeypatch)
    r = client.get("/composites/Q000001")
    assert r.status_code == 200
    body = r.json()
    assert body["composite"]["q_number"] == "Q000001"
    assert body["exemplars"] == [] and body["related"] == []


def test_composite_detail_404(monkeypatch):
    """An unknown Q-number is a 404, not a 500 or a null composite."""
    from api.repositories.composite_repo import CompositeRepository

    monkeypatch.setattr(
        CompositeRepository, "find_by_q_number", lambda self, q: None
    )

    client = _make_client(monkeypatch)
    r = client.get("/composites/Q999999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


# ── Dictionary (repo-backed) ───────────────────────────────────────────────────


def test_dictionary_browse_defaults_to_lemmas(monkeypatch):
    """No ?level= browses lemmas."""
    from api.repositories.lexical_repo import LexicalRepository

    seen = {}

    def _browse_lemmas(self, **kw):
        seen.update(kw)
        return _LEMMA_PAGE

    monkeypatch.setattr(LexicalRepository, "browse_lemmas", _browse_lemmas)

    client = _make_client(monkeypatch)
    r = client.get("/dictionary/browse")
    assert r.status_code == 200
    assert r.json()["items"][0]["lemma"] == "lugal"
    assert seen["page"] == 1 and seen["per_page"] == 50


def test_dictionary_browse_signs_level(monkeypatch):
    """?level=signs routes to browse_signs."""
    from api.repositories.lexical_repo import LexicalRepository

    called = {"signs": 0, "lemmas": 0}
    monkeypatch.setattr(
        LexicalRepository,
        "browse_signs",
        lambda self, **kw: called.__setitem__("signs", called["signs"] + 1) or {"items": []},
    )
    monkeypatch.setattr(
        LexicalRepository,
        "browse_lemmas",
        lambda self, **kw: called.__setitem__("lemmas", called["lemmas"] + 1) or {"items": []},
    )

    client = _make_client(monkeypatch)
    r = client.get("/dictionary/browse?level=signs")
    assert r.status_code == 200
    assert called["signs"] == 1 and called["lemmas"] == 0


def test_dictionary_unknown_level_falls_back_to_lemmas(monkeypatch):
    """A bogus ?level= is coerced to the lemmas branch (the else-default), so it
    renders instead of 500-ing or 404-ing."""
    from api.repositories.lexical_repo import LexicalRepository

    called = {"lemmas": 0}
    monkeypatch.setattr(
        LexicalRepository,
        "browse_lemmas",
        lambda self, **kw: called.__setitem__("lemmas", called["lemmas"] + 1) or _LEMMA_PAGE,
    )

    client = _make_client(monkeypatch)
    r = client.get("/dictionary/browse?level=bogus")
    assert r.status_code == 200
    assert called["lemmas"] == 1


def test_lemma_detail_404(monkeypatch):
    """A missing lemma id is a 404."""
    from api.repositories.lexical_repo import LexicalRepository

    monkeypatch.setattr(LexicalRepository, "get_lemma_detail", lambda self, i: None)

    client = _make_client(monkeypatch)
    r = client.get("/dictionary/lemmas/424242")
    assert r.status_code == 404
    assert r.json()["detail"] == "Lemma not found"


# ── Scholars (raw SQL — scripted cursor) ───────────────────────────────────────


def test_scholars_list_envelope_and_pagination(monkeypatch):
    """GET /scholars runs COUNT then the page SELECT; the route computes
    total_pages from total/per_page. Two queued results feed those two fetches."""
    scholar_row = {
        "id": 1,
        "name": "Enheduanna",
        "normalized_name": "enheduanna",
        "orcid": None,
        "institution": "Ur",
        "expertise_periods": None,
        "expertise_languages": None,
        "author_type": "person",
        "artifact_count": 3,
    }
    # 1) COUNT(*) -> {"n": 7}  2) page rows -> [scholar_row]
    client = _make_client(monkeypatch, results=[{"n": 7}, [scholar_row]])
    r = client.get("/scholars?per_page=3")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 7
    assert body["per_page"] == 3
    # 7 rows / 3 per page = 3 pages (ceil).
    assert body["total_pages"] == 3
    assert body["items"][0]["name"] == "Enheduanna"


def test_scholars_list_empty(monkeypatch):
    """No matching scholars => empty items, total 0, zero pages — not a 500."""
    client = _make_client(monkeypatch, results=[{"n": 0}, []])
    r = client.get("/scholars")
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == [] and body["total"] == 0
    assert body["total_pages"] == 0


def test_scholars_facets_shape(monkeypatch):
    """GET /scholars/facets runs three queries: institution facet (fetchall),
    the with/without-orcid row (fetchone), and the denominator COUNT (fetchone).
    The response must carry {total, institution, has_orcid:{with,without}}."""
    institutions = [{"value": "Yale", "n": 5}]
    orcid_row = {"with_orcid": 4, "without_orcid": 6}
    denom = {"n": 10}
    client = _make_client(monkeypatch, results=[institutions, orcid_row, denom])
    r = client.get("/scholars/facets")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 10
    assert body["has_orcid"] == {"with": 4, "without": 6}
    assert body["institution"] == [{"value": "Yale", "label": "Yale", "count": 5}]


def test_scholar_detail_404(monkeypatch):
    """A missing scholar id is a 404 (the single SELECT returns no row)."""
    client = _make_client(monkeypatch, results=[None])
    r = client.get("/scholars/999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Scholar not found"


def test_scholar_detail_unverified_claim_hides_bio(monkeypatch):
    """A scholar row with no approved claim must expose no public bio/avatar and
    report claim.verified == False — the #17 privacy gate. Regression guard: a
    handler change that leaked the ingested bio without a verified claim would
    flip these assertions."""
    row = {
        "id": 1,
        "name": "Enheduanna",
        "normalized_name": "enheduanna",
        "orcid": None,
        "active_since": None,
        "author_type": "person",
        "institution": "Ur",
        "expertise_periods": None,
        "expertise_languages": None,
        "ingested_institution": "Ur",
        "ingested_expertise_periods": None,
        "ingested_expertise_languages": None,
        "bio": "SHOULD NOT LEAK",
        "homepage_url": "https://example.org",
        "institution_overridden": False,
        "expertise_periods_overridden": False,
        "expertise_languages_overridden": False,
        "claim_id": None,
        "claim_status": None,  # no approved claim
        "claim_verified_at": None,
        "claim_method": None,
        "claimant_display_name": None,
        "claimant_avatar_url": None,
    }
    client = _make_client(monkeypatch, results=[row])
    r = client.get("/scholars/1")
    assert r.status_code == 200
    body = r.json()
    assert body["claim"]["verified"] is False
    assert body["bio"] is None
    assert body["homepage_url"] is None
    assert body["avatar_url"] is None


# ── Dashboard / home data endpoints (stats, repo-backed) ───────────────────────


def test_kpi_returns_repo_payload(monkeypatch):
    """GET /stats/kpi passes the repository's KPI dict straight through."""
    from api.repositories.stats_repo import StatsRepository

    monkeypatch.setattr(StatsRepository, "get_kpi", lambda self: _KPI)

    client = _make_client(monkeypatch)
    r = client.get("/stats/kpi")
    assert r.status_code == 200
    assert r.json()["top_periods"][0]["label"] == "Ur III"


def test_kpi_survives_empty_payload(monkeypatch):
    """A degraded/empty KPI (e.g. before any ingest) must not 500 the dashboard."""
    from api.repositories.stats_repo import StatsRepository

    monkeypatch.setattr(StatsRepository, "get_kpi", lambda self: {})

    client = _make_client(monkeypatch)
    r = client.get("/stats/kpi")
    assert r.status_code == 200
    assert r.json() == {}


def test_coverage_gaps_wraps_items(monkeypatch):
    """GET /stats/coverage-gaps wraps the repo list in an {items:[...]} envelope
    and returns an empty list (not a 500) when line-ref data isn't populated."""
    from api.repositories.stats_repo import StatsRepository

    monkeypatch.setattr(
        StatsRepository,
        "get_coverage_gaps",
        lambda self, min_exemplars=5, limit=4: [],
    )

    client = _make_client(monkeypatch)
    r = client.get("/stats/coverage-gaps")
    assert r.status_code == 200
    assert r.json() == {"items": []}
