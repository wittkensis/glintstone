"""Timing instrumentation and search-pipeline behaviour tests.

Covers the phase-level timing added in the performance audit:
- search() emits a structured log line with all phase durations
- Voyage cache emits hit/miss log lines
- Degraded paths (semantic failure, no Voyage client) fall back correctly
- RRF fusion produces deterministic ordering across varied input shapes
- Edge cases: empty query, single-char query, very long query, unicode
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch


from core.agent.search_engine import (
    SearchEngine,
    SearchHit,
    _QUERY_VEC_CACHE,
    _cached_query_vector,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _hit(entity_type: str, entity_id: str, score: float = 0.5) -> SearchHit:
    return SearchHit(
        entity_type=entity_type,
        entity_id=entity_id,
        primary_label=entity_id,
        secondary_label=None,
        sources=[],
        score=score,
    )


def _fake_conn(rows: list[dict] | None = None):
    """Minimal psycopg Connection stub returning canned rows."""
    cur = MagicMock()
    cur.fetchall.return_value = rows or []
    cur.fetchone.return_value = None
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn


# ── Voyage cache logging ──────────────────────────────────────────────────────


def test_voyage_cache_miss_logs_embed_duration(caplog):
    """A cold cache hit should log 'voyage embed duration_ms=...'."""
    _QUERY_VEC_CACHE.clear()
    fake_voyage = MagicMock()
    fake_voyage.embed_query.return_value = MagicMock(vector=[0.1, 0.2, 0.3])

    with caplog.at_level(logging.INFO, logger="core.agent.search_engine"):
        _cached_query_vector(fake_voyage, "Ur III tablets")

    assert any(
        "voyage embed" in r.message and "duration_ms=" in r.message
        for r in caplog.records
    )
    fake_voyage.embed_query.assert_called_once()


def test_voyage_cache_hit_logs_debug_and_skips_embed(caplog):
    """A warm cache hit should log 'voyage cache hit' at DEBUG and skip embed_query."""
    _QUERY_VEC_CACHE.clear()
    fake_voyage = MagicMock()
    fake_voyage.embed_query.return_value = MagicMock(vector=[0.1, 0.2, 0.3])

    # Prime the cache
    _cached_query_vector(fake_voyage, "Gilgamesh")
    fake_voyage.embed_query.reset_mock()

    with caplog.at_level(logging.DEBUG, logger="core.agent.search_engine"):
        _cached_query_vector(fake_voyage, "Gilgamesh")

    assert any("voyage cache hit" in r.message for r in caplog.records)
    fake_voyage.embed_query.assert_not_called()


def test_voyage_cache_is_query_specific():
    """Two different queries should produce two embed calls."""
    _QUERY_VEC_CACHE.clear()
    fake_voyage = MagicMock()
    fake_voyage.embed_query.return_value = MagicMock(vector=[0.1])

    _cached_query_vector(fake_voyage, "Nippur")
    _cached_query_vector(fake_voyage, "Lagash")
    assert fake_voyage.embed_query.call_count == 2


# ── Phase-level timing log line ───────────────────────────────────────────────


def test_search_emits_timing_log_for_lexical_mode(caplog):
    """search() must log a timing summary line for every call."""
    engine = SearchEngine(voyage=None)
    conn = _fake_conn()

    with caplog.at_level(logging.INFO, logger="core.agent.search_engine"):
        from core.schemas.search import SearchParams

        params = SearchParams(q="šarru", mode="lexical", limit=5)
        engine.search(conn, params)

    timing_records = [r for r in caplog.records if "total_ms=" in r.message]
    assert len(timing_records) == 1
    msg = timing_records[0].message
    assert "retrieval_ms=" in msg
    assert "count_ms=" in msg
    assert "hydrate_ms=" in msg
    assert "mode=lexical" in msg


def test_search_timing_log_includes_hit_counts(caplog):
    """Timing log should surface lexical_hits and semantic_hits counts."""
    engine = SearchEngine(voyage=None)
    conn = _fake_conn()

    with caplog.at_level(logging.INFO, logger="core.agent.search_engine"):
        from core.schemas.search import SearchParams

        params = SearchParams(q="king", mode="lexical", limit=5)
        engine.search(conn, params)

    msg = next(r.message for r in caplog.records if "total_ms=" in r.message)
    assert "lexical_hits=" in msg
    assert "semantic_hits=" in msg


def test_search_timing_log_query_truncated_at_60_chars(caplog):
    """Long queries should be truncated in the log line (privacy + noise)."""
    engine = SearchEngine(voyage=None)
    conn = _fake_conn()
    long_q = "a" * 200

    with caplog.at_level(logging.INFO, logger="core.agent.search_engine"):
        from core.schemas.search import SearchParams

        params = SearchParams(q=long_q, mode="lexical", limit=5)
        engine.search(conn, params)

    msg = next(r.message for r in caplog.records if "total_ms=" in r.message)
    # The logged query repr should be at most 60 chars of the original + quotes
    assert long_q not in msg  # full 200-char string must not appear


# ── Degraded-path fallbacks ───────────────────────────────────────────────────


def test_hybrid_without_voyage_falls_back_to_lexical(caplog):
    """hybrid mode with no Voyage client must silently use lexical only."""
    engine = SearchEngine(voyage=None)
    conn = _fake_conn()

    with caplog.at_level(logging.INFO, logger="core.agent.search_engine"):
        from core.schemas.search import SearchParams

        params = SearchParams(q="temple", mode="hybrid", limit=5)
        engine.search(conn, params)

    # Should not raise; should emit a timing line showing 0 semantic hits
    msg = next(r.message for r in caplog.records if "total_ms=" in r.message)
    assert "semantic_hits=0" in msg


def test_hybrid_semantic_exception_logs_warning_and_continues(caplog):
    """If the semantic sub-call raises, a warning is logged and results still return."""
    fake_voyage = MagicMock()
    fake_voyage.embed_query.side_effect = ConnectionError("Voyage down")
    engine = SearchEngine(voyage=fake_voyage)
    conn = _fake_conn()

    with caplog.at_level(logging.WARNING, logger="core.agent.search_engine"):
        from core.schemas.search import SearchParams

        params = SearchParams(q="temple", mode="hybrid", limit=5)
        result = engine.search(conn, params)

    warning_msgs = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert any("semantic" in m or "voyage" in m.lower() for m in warning_msgs)
    # search must still return a valid result object
    assert result is not None


# ── Edge-case input handling ──────────────────────────────────────────────────


def test_search_empty_query_returns_empty_groups():
    engine = SearchEngine(voyage=None)
    conn = _fake_conn()
    from core.schemas.search import SearchParams

    params = SearchParams(q="", mode="lexical", limit=5)
    result = engine.search(conn, params)
    # All groups should be empty lists
    assert all(len(v) == 0 for v in result.groups.values())


def test_search_whitespace_query_returns_empty_groups():
    engine = SearchEngine(voyage=None)
    conn = _fake_conn()
    from core.schemas.search import SearchParams

    params = SearchParams(q="   ", mode="lexical", limit=5)
    result = engine.search(conn, params)
    assert all(len(v) == 0 for v in result.groups.values())


def test_search_unicode_query_does_not_raise():
    """Cuneiform and accented characters in queries must not raise."""
    engine = SearchEngine(voyage=None)
    conn = _fake_conn()
    from core.schemas.search import SearchParams

    for q in ["šarru", "𒀭𒂗𒍪", "Ṣilli-Adad", "lugal-àm"]:
        params = SearchParams(q=q, mode="lexical", limit=5)
        result = engine.search(conn, params)
        assert result is not None


def test_search_p_number_exact_match_short_circuits(caplog):
    """A valid P-number query should hit the exact-match fast path."""
    engine = SearchEngine(voyage=None)
    # Return a valid artifact row for P000001
    conn = _fake_conn()
    conn.cursor.return_value.fetchone.return_value = {
        "designation": "Old Babylonian tablet",
        "period_normalized": "Old Babylonian",
        "provenience_normalized": "Nippur",
    }

    from core.schemas.search import SearchParams

    params = SearchParams(q="P000001", mode="hybrid", limit=5)
    result = engine.search(conn, params)

    tablet_hits = result.groups.get("tablets", [])
    assert any(h.entity_id == "P000001" for h in tablet_hits)


def test_search_respects_limit_per_type():
    """Results per entity_type should never exceed params.limit."""
    engine = SearchEngine(voyage=None)
    conn = _fake_conn()
    from core.schemas.search import SearchParams

    # Inject many fake hits via the RRF path
    many_hits = [_hit("tablets", f"P{i:06d}", score=1.0 - i * 0.01) for i in range(50)]
    with (
        patch.object(engine, "_lexical_search", return_value=many_hits),
        patch.object(engine, "_count_per_type", return_value={}),
        patch.object(engine, "_hydrate_tablet_extras", return_value=None),
    ):
        params = SearchParams(q="any", mode="lexical", limit=5)
        result = engine.search(conn, params)

    assert len(result.groups.get("tablets", [])) <= 5


# ── RRF determinism ───────────────────────────────────────────────────────────


def test_rrf_is_deterministic_for_same_input():
    """Running RRF twice on the same lists should produce identical ordering."""
    engine = SearchEngine(voyage=None)
    lexical = [_hit("tablets", f"P{i}", score=0.9 - i * 0.1) for i in range(5)]
    semantic = [_hit("tablets", f"P{i}", score=0.8 - i * 0.1) for i in range(5)]
    run1 = [h.entity_id for h in engine._rrf([lexical, semantic])]
    run2 = [h.entity_id for h in engine._rrf([lexical, semantic])]
    assert run1 == run2


def test_rrf_score_increases_with_dual_list_presence():
    """An item in both lists must outscore any item in only one list."""
    engine = SearchEngine(voyage=None)
    shared = _hit("tablets", "P_BOTH", score=0.3)
    lex_only = _hit("tablets", "P_LEX", score=0.99)
    sem_only = _hit("tablets", "P_SEM", score=0.99)

    fused = engine._rrf([[shared, lex_only], [shared, sem_only]])
    ids = [h.entity_id for h in fused]
    assert ids[0] == "P_BOTH"


# ── #253 popular-query warm cache ─────────────────────────────────────────────


def test_warm_query_cache_pins_and_skips_cold_embed():
    """warm_query_cache pre-embeds queries and PINS them so a later lookup is a
    hit with no further embed call (#253: kills the cold ~1.4-1.9s hero path)."""
    from core.agent.search_engine import warm_query_cache

    _QUERY_VEC_CACHE.clear()
    voyage = MagicMock()
    voyage.embed.return_value = [
        MagicMock(vector=[0.1, 0.2, 0.3]),
        MagicMock(vector=[0.4, 0.5, 0.6]),
    ]
    n = warm_query_cache(voyage, queries=["barley rations", "royal inscriptions"])
    assert n == 2
    assert voyage.embed.call_count == 1  # ONE batched call for the whole list

    # A subsequent lookup is a pinned hit — embed_query must never be called.
    vec = _cached_query_vector(voyage, "barley rations")
    assert vec == [0.1, 0.2, 0.3]
    voyage.embed_query.assert_not_called()


def test_warm_query_cache_pin_survives_ttl():
    """A pinned entry must NOT expire after the 5-minute TTL (#253)."""
    import hashlib

    from core.agent.search_engine import warm_query_cache

    _QUERY_VEC_CACHE.clear()
    voyage = MagicMock()
    voyage.embed.return_value = [MagicMock(vector=[0.7, 0.8, 0.9])]
    warm_query_cache(voyage, queries=["land sale"])

    # Force the stored timestamp far into the past (well past the TTL).
    h = hashlib.sha256("land sale".encode()).hexdigest()
    stored_at, vector, pinned = _QUERY_VEC_CACHE[h]
    _QUERY_VEC_CACHE[h] = (stored_at - 10_000, vector, pinned)

    vec = _cached_query_vector(voyage, "land sale")  # still a hit
    assert vec == [0.7, 0.8, 0.9]
    voyage.embed_query.assert_not_called()


def test_warm_query_cache_no_voyage_is_noop():
    """No Voyage client → warm pass is a safe no-op returning 0 (never raises)."""
    from core.agent.search_engine import warm_query_cache

    _QUERY_VEC_CACHE.clear()
    assert warm_query_cache(None) == 0


def test_warm_query_cache_swallows_embed_failure():
    """A Voyage hiccup during warming must not raise — queries just stay cold."""
    from core.agent.search_engine import warm_query_cache

    _QUERY_VEC_CACHE.clear()
    voyage = MagicMock()
    voyage.embed.side_effect = RuntimeError("voyage down")
    assert warm_query_cache(voyage, queries=["letters"]) == 0
