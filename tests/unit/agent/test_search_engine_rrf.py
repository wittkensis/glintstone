"""RRF fusion is pure math — exercise without a DB."""

from core.agent.search_engine import SearchEngine, SearchHit


def _hit(entity_type: str, entity_id: str, score: float) -> SearchHit:
    return SearchHit(
        entity_type=entity_type,
        entity_id=entity_id,
        primary_label=entity_id,
        secondary_label=None,
        sources=[],
        score=score,
    )


def test_rrf_promotes_items_present_in_both_lists():
    engine = SearchEngine(voyage=None)
    lexical = [_hit("tablets", "P1", 0.9), _hit("tablets", "P2", 0.5)]
    semantic = [_hit("tablets", "P2", 0.8), _hit("tablets", "P3", 0.7)]
    fused = engine._rrf([lexical, semantic])
    ids = [h.entity_id for h in fused]
    # P2 appears in both → should rank above either single-list entry
    assert ids[0] == "P2"
    # P1 and P3 each appear in one list
    assert set(ids[1:]) == {"P1", "P3"}


def test_rrf_handles_empty_lists():
    engine = SearchEngine(voyage=None)
    fused = engine._rrf([[], []])
    assert fused == []


def test_rrf_preserves_hit_metadata():
    engine = SearchEngine(voyage=None)
    h = SearchHit(
        entity_type="lemmas",
        entity_id="42",
        primary_label="šarru",
        secondary_label="king • N • akk",
        sources=["epsd2"],
        score=0.7,
        int_ref=42,
    )
    fused = engine._rrf([[h], []])
    assert fused[0].primary_label == "šarru"
    assert fused[0].sources == ["epsd2"]
    assert fused[0].int_ref == 42
