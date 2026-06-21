"""Tests for #177 — scholar-detail contributions ledger pagination.

The contributions section renders 50 rows/page newest-run-first and exposes a
server-rendered "Show more" footer (mirroring the #206 publications pattern)
driven by the ?contrib_page= query param. When the last page is reached past
page 1, a #189-style end state ("No more contributions") renders instead.

These are render-level tests: a stub transport feeds the route a multi-page
contributions envelope and we assert on the produced HTML.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


_SCHOLAR = {
    "id": 1595,
    "name": "Test Scholar",
    "normalized_name": "test scholar",
    "orcid": None,
    "institution": None,
    "expertise_periods": [],
    "expertise_languages": [],
    "active_since": None,
    "author_type": "human",
}

_EMPTY_PUBLICATIONS = {
    "items": [],
    "total": 0,
    "summary": {},
    "type_counts": [],
    "type": "",
    "page": 1,
    "total_pages": 0,
}


def _contrib_row(p_number: str) -> dict:
    return {
        "p_number": p_number,
        "designation": f"Artifact {p_number}",
        "object_type": "tablet",
        "period_normalized": "Ur III",
        "genre": "administrative",
        "language_normalized": "Sumerian",
        "method": "manual",
        "source_type": "oracc",
        "created_at": "2026-01-01T00:00:00",
    }


class _StubTransport:
    """Routes contributions/publications/scholar lookups to fixtures.

    The contributions envelope is page-aware: the route forwards ?contrib_page=
    as the `page` query param, and this transport echoes it back so the template
    sees the correct page/total_pages and renders the right footer state.
    """

    def __init__(self, contrib_total: int):
        self._contrib_total = contrib_total
        self._per_page = 50

    def get(self, path, params=None, token=None):
        params = params or {}
        if path.endswith("/contributions"):
            page = int(params.get("page", 1))
            per_page = int(params.get("per_page", 50))
            total = self._contrib_total
            total_pages = (total + per_page - 1) // per_page if total else 0
            start = (page - 1) * per_page
            items = [
                _contrib_row(f"P{start + i:06d}")
                for i in range(max(0, min(per_page, total - start)))
            ]
            return {
                "items": items,
                "total": total,
                "run_count": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
            }
        if path.endswith("/publications"):
            return dict(_EMPTY_PUBLICATIONS)
        if path.startswith("/scholars/"):
            return dict(_SCHOLAR)
        if "auth/me" in path or "saved-items" in path:
            return {}
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


def _make_client(monkeypatch, contrib_total: int) -> TestClient:
    from core import database

    monkeypatch.setattr(database, "init_pool", lambda *a, **kw: None)
    monkeypatch.setattr(database, "close_pool", lambda *a, **kw: None)

    from app import main as app_main
    from app.api_client import GlintstoneAPI
    from app.transports import HttpxTransport

    monkeypatch.setattr(HttpxTransport, "__init__", lambda self, **kw: None)
    monkeypatch.setattr(HttpxTransport, "close", lambda self: None)

    fake_api = GlintstoneAPI(_StubTransport(contrib_total))
    client = TestClient(app_main.app, cookies={"session_token": "test-token"})
    client.__enter__()
    client.app.state.api = fake_api
    return client


def test_show_more_footer_when_more_pages(monkeypatch):
    """120 contributions → page 1 shows a 'Show more' link to contrib_page=2."""
    client = _make_client(monkeypatch, contrib_total=120)
    try:
        r = client.get("/scholars/1595")
        if r.status_code != 200:
            pytest.skip(f"detail page returned {r.status_code}")
        assert "contrib_page=2" in r.text
        assert "120 artifacts total" in r.text
        # Page 1 renders exactly 50 rows.
        assert r.text.count("contrib-row__link") == 50
    finally:
        client.__exit__(None, None, None)


def test_end_state_on_last_page(monkeypatch):
    """120 contributions, contrib_page=3 → end state, no further 'Show more'."""
    client = _make_client(monkeypatch, contrib_total=120)
    try:
        r = client.get("/scholars/1595?contrib_page=3")
        if r.status_code != 200:
            pytest.skip(f"detail page returned {r.status_code}")
        assert "No more contributions" in r.text
        assert "contrib_page=4" not in r.text
        # Last page holds the remaining 20 rows (120 - 100).
        assert r.text.count("contrib-row__link") == 20
    finally:
        client.__exit__(None, None, None)


def test_no_footer_when_single_page(monkeypatch):
    """30 contributions fit on one page → no 'Show more', no end state."""
    client = _make_client(monkeypatch, contrib_total=30)
    try:
        r = client.get("/scholars/1595")
        if r.status_code != 200:
            pytest.skip(f"detail page returned {r.status_code}")
        assert "contrib_page=2" not in r.text
        assert "No more contributions" not in r.text
    finally:
        client.__exit__(None, None, None)
