"""Unit tests for the scholar publications query layer + route (#607 / #206).

The ``GET /scholars/{id}/publications`` endpoint sources a scholar's
bibliographic works through the ``publication_authors`` junction. These tests
run WITHOUT a live database — they exercise:

  1. ``PublicationRepository`` against a hand-rolled fake psycopg connection, so
     the SQL-shaping and result-mapping logic is verified in isolation (the
     "core logic to source publications" #607 asks for); and
  2. the route function directly with a fake connection, so the 404 guard, the
     ``?type=`` whitelist, and the pagination/total math are covered without
     standing up the full FastAPI app or a Postgres.

Deliberately mocked, not DB-backed: the live query is separately proven against
the production database in the task report (real rows for scholar #1397). These
tests pin the *contract* so a future refactor can't silently change the shape.
"""

import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.repositories.publication_repo import (  # noqa: E402
    PUBLICATION_TYPES,
    PublicationRepository,
)
from api.routes.scholars import get_scholar_publications  # noqa: E402


# ── Fake DB scaffolding ─────────────────────────────────────────────────────


class FakeCursor:
    """A cursor whose ``fetchone``/``fetchall`` are driven by a queue of canned
    results, one entry consumed per ``execute``. Each entry is either a single
    dict (for ``fetchone``) or a list of dicts (for ``fetchall``)."""

    def __init__(self, results: list):
        self._results = list(results)
        self._current = None
        self.executed: list[tuple[str, object]] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=()):
        self.executed.append((sql, params))
        self._current = self._results.pop(0) if self._results else None

    def fetchone(self):
        cur = self._current
        if isinstance(cur, list):
            return cur[0] if cur else None
        return cur

    def fetchall(self):
        cur = self._current
        if cur is None:
            return []
        return cur if isinstance(cur, list) else [cur]


class FakeConn:
    """A psycopg-shaped connection yielding a shared FakeCursor."""

    def __init__(self, results: list):
        self._cursor = FakeCursor(results)

    def cursor(self, *a, **k):
        return self._cursor


# ── Repository unit tests ───────────────────────────────────────────────────


def test_publication_types_matches_enum():
    """The whitelist mirrors the DB CHECK constraint's 15 values exactly — a
    drift here would silently drop a valid ``?type=`` filter."""
    assert PUBLICATION_TYPES == frozenset(
        {
            "monograph",
            "edited_volume",
            "journal_article",
            "series_volume",
            "digital_edition",
            "museum_catalog",
            "dissertation",
            "conference_paper",
            "hand_copy_publication",
            "chapter",
            "proceedings",
            "thesis",
            "report",
            "unpublished",
            "other",
        }
    )
    assert len(PUBLICATION_TYPES) == 15


def test_scholar_exists_true_and_false():
    assert PublicationRepository(FakeConn([{"?column?": 1}])).scholar_exists(1) is True
    assert PublicationRepository(FakeConn([None])).scholar_exists(999) is False


def test_works_summary_maps_and_coerces():
    conn = FakeConn(
        [
            {  # aggregate row
                "works": 2346,
                "total_cites": 9,
                "top_cites": 7,
                "first_year": 1985,
                "last_year": 2026,
                "type_count": 5,
            },
            {"tablets_edited": 60},  # tablets-edited row
        ]
    )
    summary = PublicationRepository(conn).works_summary(1397)
    assert summary == {
        "works": 2346,
        "total_cites": 9,
        "top_cites": 7,
        "first_year": 1985,
        "last_year": 2026,
        "type_count": 5,
        "tablets_edited": 60,
    }


def test_works_summary_empty_scholar_yields_zeroes():
    """A scholar with no works: aggregates come back all-null; the mapping must
    coerce to honest zeroes/None, never blow up."""
    conn = FakeConn(
        [
            {
                "works": 0,
                "total_cites": 0,
                "top_cites": None,
                "first_year": None,
                "last_year": None,
                "type_count": 0,
            },
            {"tablets_edited": 0},
        ]
    )
    summary = PublicationRepository(conn).works_summary(42)
    assert summary["works"] == 0
    assert summary["total_cites"] == 0
    assert summary["top_cites"] is None
    assert summary["tablets_edited"] == 0


def test_type_breakdown_maps_rows():
    conn = FakeConn(
        [[{"type": "journal_article", "n": 2235}, {"type": "other", "n": 107}]]
    )
    assert PublicationRepository(conn).type_breakdown(1397) == [
        {"type": "journal_article", "count": 2235},
        {"type": "other", "count": 107},
    ]


def test_list_works_binds_type_filter_when_present():
    conn = FakeConn([[{"id": 1, "title": "X", "role": "author", "position": 1}]])
    repo = PublicationRepository(conn)
    rows = repo.list_works(1397, limit=50, offset=0, type_filter="journal_article")
    assert rows == [{"id": 1, "title": "X", "role": "author", "position": 1}]
    sql, params = conn._cursor.executed[-1]
    assert "AND p.publication_type = %s" in sql
    # scholar_id, type_filter, limit, offset  (type bound as a parameter)
    assert params == (1397, "journal_article", 50, 0)


def test_list_works_omits_type_clause_when_absent():
    conn = FakeConn([[]])
    PublicationRepository(conn).list_works(1397, limit=50, offset=100)
    sql, params = conn._cursor.executed[-1]
    assert "AND p.publication_type" not in sql
    assert params == (1397, 50, 100)  # no type param


# ── Route-level tests (fake conn, no app) ───────────────────────────────────


def _route_conn(exists: bool, *, works: int, breakdown: list, rows: list):
    """Assemble the exact result queue the route consumes in order:
    scholar_exists → summary-agg → tablets-edited → type_breakdown → list_works.
    """
    results: list = [{"1": 1} if exists else None]
    if exists:
        results.append(
            {
                "works": works,
                "total_cites": 0,
                "top_cites": None,
                "first_year": None,
                "last_year": None,
                "type_count": len(breakdown),
            }
        )
        results.append({"tablets_edited": 0})
        # type_breakdown rows come back keyed {type, n} (the SQL alias); the
        # repo maps n -> count. Rebuild the fake rows in that raw shape.
        results.append([{"type": b["type"], "n": b["count"]} for b in breakdown])
        results.append(rows)
    return FakeConn(results)


def test_route_404_for_unknown_scholar():
    conn = _route_conn(False, works=0, breakdown=[], rows=[])
    with pytest.raises(HTTPException) as exc:
        get_scholar_publications(scholar_id=999999, page=1, per_page=50, conn=conn)
    assert exc.value.status_code == 404


def test_route_unfiltered_total_equals_works_and_paginates():
    rows = [{"id": 33064, "title": "Esarhaddon", "role": "author", "position": 1}]
    breakdown = [
        {"type": "journal_article", "count": 2235},
        {"type": "other", "count": 111},
    ]
    conn = _route_conn(True, works=2346, breakdown=breakdown, rows=rows)
    out = get_scholar_publications(scholar_id=1397, page=1, per_page=50, conn=conn)

    assert out["total"] == 2346  # whole-corpus works
    assert out["total_pages"] == (2346 + 49) // 50  # 47
    assert out["items"] == rows
    assert out["summary"]["works"] == 2346
    assert out["type_counts"] == breakdown
    assert out["type"] == ""  # no filter active


def test_route_type_filter_narrows_total_to_that_type():
    breakdown = [
        {"type": "journal_article", "count": 2235},
        {"type": "other", "count": 111},
    ]
    conn = _route_conn(True, works=2346, breakdown=breakdown, rows=[])
    out = get_scholar_publications(
        scholar_id=1397, page=1, per_page=50, type="other", conn=conn
    )
    # total reflects the active filter's count from the breakdown, not works.
    assert out["total"] == 111
    assert out["type"] == "other"
    # ...but the summary + pills stay whole-corpus so counts don't collapse.
    assert out["summary"]["works"] == 2346
    assert out["type_counts"] == breakdown


def test_route_bad_type_filter_is_ignored():
    breakdown = [{"type": "journal_article", "count": 2235}]
    conn = _route_conn(True, works=2235, breakdown=breakdown, rows=[])
    out = get_scholar_publications(
        scholar_id=1397, page=1, per_page=50, type="not-a-real-type", conn=conn
    )
    # Unknown type is dropped: filter inert, total falls back to whole-corpus.
    assert out["type"] == ""
    assert out["total"] == 2235
