"""Unit tests for LexicalRepository.get_lemma_attestation_periods (#201).

These exercise the orchestration logic — 404 vs empty, the per-period payload
shape, and the dated/undated split — without a live database by stubbing the
two fetch helpers the method calls. The actual SQL (the #176 join grouped by a
de-duplicated period_canon) is validated against prod in the build's
data-availability gate; here we lock the contract the route, web layer, and the
LemmaPeriodTimeline JS depend on.
"""

from __future__ import annotations

from api.repositories.lexical_repo import LexicalRepository


def _repo() -> LexicalRepository:
    # BaseRepository.__init__ only stores the connection; we never touch it
    # because every fetch_* is stubbed per-test.
    return LexicalRepository(conn=None)  # type: ignore[arg-type]


def test_missing_lemma_returns_none():
    """A non-existent lemma id yields None so the route can 404."""
    repo = _repo()
    repo.fetch_one = lambda sql, params=(): None  # type: ignore[assignment]
    assert repo.get_lemma_attestation_periods(999999) is None


def test_existing_lemma_no_datable_periods_returns_empty_periods():
    """An existing lemma whose tablets are all undatable returns an empty
    `periods` list (page renders the #189 empty state), not None."""
    repo = _repo()
    calls = {"n": 0}

    def fake_one(sql, params=()):
        calls["n"] += 1
        if calls["n"] == 1:  # lemma lookup
            return {"citation_form": "ḫapû", "guide_word": "rare"}
        return {"undated_tablets": 4}  # undated count query

    repo.fetch_one = fake_one  # type: ignore[assignment]
    repo.fetch_all = lambda sql, params=(): []  # type: ignore[assignment]

    result = repo.get_lemma_attestation_periods(42)
    assert result is not None
    assert result["periods"] == []
    assert result["dated_tablet_count"] == 0
    assert result["undated_tablet_count"] == 4
    assert result["citation_form"] == "ḫapû"


def test_period_distribution_payload_shape():
    """Per-period rows become the `periods` array; dated total is summed and
    the undated count is carried through verbatim."""
    repo = _repo()
    calls = {"n": 0}
    rows = [
        {
            "canonical": "Ur III",
            "date_start_bce": 2100,
            "date_end_bce": 2000,
            "sort_order": 100,
            "tablet_count": 258,
        },
        {
            "canonical": "Old Babylonian",
            "date_start_bce": 1900,
            "date_end_bce": 1600,
            "sort_order": 120,
            "tablet_count": 341,
        },
    ]

    def fake_one(sql, params=()):
        calls["n"] += 1
        if calls["n"] == 1:
            return {"citation_form": "šarru", "guide_word": "king"}
        return {"undated_tablets": 2967}

    repo.fetch_one = fake_one  # type: ignore[assignment]
    repo.fetch_all = lambda sql, params=(): rows  # type: ignore[assignment]

    result = repo.get_lemma_attestation_periods(469865)
    assert result is not None
    assert result["citation_form"] == "šarru"
    assert result["guide_word"] == "king"
    assert len(result["periods"]) == 2
    first = result["periods"][0]
    assert first == {
        "period": "Ur III",
        "date_start_bce": 2100,
        "date_end_bce": 2000,
        "tablet_count": 258,
    }
    # sort_order is consumed for ordering but not leaked into the payload.
    assert "sort_order" not in first
    assert result["dated_tablet_count"] == 258 + 341
    assert result["undated_tablet_count"] == 2967
