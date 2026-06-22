"""Unit tests for LexicalRepository.get_lemma_attestations (#176).

These exercise the orchestration logic — 404 vs empty, pagination math, and
the shape of the returned payload — without a live database by stubbing the
two fetch helpers the method calls. The actual SQL is validated against prod
in the build's data-availability gate; here we lock the contract the route and
template depend on.
"""

from __future__ import annotations

from api.repositories.lexical_repo import LexicalRepository


def _repo() -> LexicalRepository:
    # The base __init__ only stores the connection; we never touch it because
    # every fetch_* is stubbed per-test.
    return LexicalRepository(conn=None)  # type: ignore[arg-type]


def test_missing_lemma_returns_none():
    """A non-existent lemma id yields None so the route can 404."""
    repo = _repo()
    repo.fetch_one = lambda sql, params=(): None  # type: ignore[assignment]
    assert repo.get_lemma_attestations(999999) is None


def test_existing_lemma_no_attestations_returns_empty_items():
    """An existing lemma with zero occurrences returns an empty list, not None
    — so the page renders the standard empty state rather than a 404."""
    repo = _repo()
    calls = {"n": 0}

    def fake_one(sql, params=()):
        calls["n"] += 1
        if calls["n"] == 1:  # lemma lookup
            return {"citation_form": "ḫapû", "guide_word": "rare"}
        return {"total_lines": 0, "tablet_count": 0}  # counts

    repo.fetch_one = fake_one  # type: ignore[assignment]
    repo.fetch_all = lambda sql, params=(): []  # type: ignore[assignment]

    result = repo.get_lemma_attestations(42)
    assert result is not None
    assert result["items"] == []
    assert result["total"] == 0
    assert result["tablet_count"] == 0
    assert result["total_pages"] == 0
    assert result["citation_form"] == "ḫapû"


def test_pagination_math_and_payload_shape():
    """Totals drive total_pages; the page of rows is passed through verbatim."""
    repo = _repo()
    calls = {"n": 0}
    rows = [
        {
            "p_number": "P202351",
            "line_number": "5",
            "raw_atf": "ina E₂ ...",
            "designation": "CT 56, 004",
            "period_normalized": None,
            "provenience_normalized": None,
            "language_normalized": "Akkadian",
        }
    ]

    def fake_one(sql, params=()):
        calls["n"] += 1
        if calls["n"] == 1:
            return {"citation_form": "bītu", "guide_word": "house"}
        return {"total_lines": 45, "tablet_count": 12}

    repo.fetch_one = fake_one  # type: ignore[assignment]
    repo.fetch_all = lambda sql, params=(): rows  # type: ignore[assignment]

    result = repo.get_lemma_attestations(7, page=2, per_page=20)
    assert result is not None
    assert result["total"] == 45
    assert result["tablet_count"] == 12
    # 45 rows at 20/page -> 3 pages
    assert result["total_pages"] == 3
    assert result["page"] == 2
    assert result["per_page"] == 20
    assert result["items"] == rows
    assert result["guide_word"] == "house"
