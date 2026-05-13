"""SearchHit's new tablet-display extras (thumbnail_url, pipeline_*).

These cover the data-shape contract the global-search drawer depends on; the
actual DB hydration is exercised by integration tests against a live Postgres.
"""

from core.agent.search_engine import SearchHit


def test_search_hit_carries_optional_display_extras():
    hit = SearchHit(
        entity_type="tablets",
        entity_id="P3928244",
        primary_label="Gilgameš tablet",
        secondary_label="Ur III",
        sources=["cdli"],
        score=0.9,
        thumbnail_url="https://r2.example/x.webp",
        pipeline_completeness=3,
        pipeline_stages=[1, 1, 1, 0, 0],
    )
    assert hit.thumbnail_url == "https://r2.example/x.webp"
    assert hit.pipeline_completeness == 3
    assert hit.pipeline_stages == [1, 1, 1, 0, 0]


def test_search_hit_extras_default_to_none():
    hit = SearchHit(
        entity_type="lemmas",
        entity_id="42",
        primary_label="šarru",
        secondary_label="king",
        sources=[],
        score=0.5,
    )
    assert hit.thumbnail_url is None
    assert hit.pipeline_completeness is None
    assert hit.pipeline_stages is None
