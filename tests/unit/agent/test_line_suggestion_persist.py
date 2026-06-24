"""Persist / read-back coverage for ``do_suggest_line_translation`` (#216).

Why this exists
---------------
#215 surfaced a class of bug that pytest could not catch: the agent_outputs
call sites drifted on a keyword name (``raw_output`` vs ``output_text``) and the
only thing that flagged it was mypy. The agentic line-suggestion feature (#109)
had *zero* tests, so a future rename of the persisted-column keyword, or a change
to the JSON shape written on the way in / read on the way out, would pass the
suite silently and only blow up against a live database.

These tests pin the **persist → read-back round-trip** of
``do_suggest_line_translation`` without a database or an Anthropic call:

1. On a cache *miss* the function persists via ``agent_outputs.insert`` — we
   capture the exact keyword arguments it passes (this fails loudly if the
   ``output_text=`` keyword is renamed, the #215 failure mode).
2. On a cache *hit* the function reads ``persisted.output_text`` back, JSON-loads
   it, and reconstructs a ``LineSuggestionPayload``. We feed it the very bytes
   captured in step 1, proving the written shape is the shape the reader expects.

If the persisted JSON shape and the read-back parser ever drift apart, the
round-trip test fails in pytest — not just under mypy, and not only in prod.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime


from api.services import agent_service
from core.agent.agent_outputs import PersistedOutput
from core.schemas.envelope import LineSuggestionPayload


class _FakeConn:
    """Stand-in for a psycopg connection. The service never touches it directly
    in these tests — every DB seam (insert / find_fresh / fact assembly) is
    monkeypatched — but the signature requires *something* to pass through."""


def _persisted_from(output_text: str) -> PersistedOutput:
    """Build a PersistedOutput exactly as ``find_fresh`` would return it."""
    return PersistedOutput(
        id=1,
        interaction_id=None,
        output_type="line_suggestion",
        target_type="line",
        target_id="P000001:obverse:1:",
        focus="suggest",
        model="claude-test",
        prompt_version="suggest-line.v1",
        output_text=output_text,
        citations=[],
        source_run_ids=[],
        best_guess_flag=False,
        generated_at=datetime.now(UTC),
    )


def test_read_back_reconstructs_payload_from_cache(monkeypatch):
    """Cache hit: the persisted JSON is read from ``output_text`` and rebuilt
    into a ``LineSuggestionPayload`` with the original fields intact."""
    payload = LineSuggestionPayload(
        line_id=42,
        atf="lugal-e",
        language="Sumerian",
        language_supported=True,
        missing_layers=["morphology"],
        model="claude-test",
        prompt_version="suggest-line.v1",
    )
    cached_text = json.dumps(
        {"summary": "Line 1: the king", "data": payload.model_dump()}
    )

    monkeypatch.setattr(
        agent_service.agent_outputs,
        "find_fresh",
        lambda conn, **kw: _persisted_from(cached_text),
    )

    resp = agent_service.do_suggest_line_translation(
        _FakeConn(),  # type: ignore[arg-type]
        p_number="P000001",
        surface_name="obverse",
        line_number="1",
        interaction_id_str="int-1",
    )

    assert resp.summary == "Line 1: the king"
    assert resp.data.line_id == 42
    assert resp.data.atf == "lugal-e"
    assert resp.data.language == "Sumerian"
    assert resp.data.missing_layers == ["morphology"]
    # Cached responses are labelled as a cached synthesis source.
    assert any(s.method == "cached-synthesis" for s in resp.sources)


def test_persisted_text_round_trips_through_read_back(monkeypatch):
    """The core anti-drift guarantee.

    Drive a cache *miss* so the function builds a payload and persists it; capture
    the exact ``output_text`` keyword it writes; then feed that captured text back
    through the read-back path and assert the payload survives the round-trip.

    This is the #215 failure class: if persist writes one keyword/shape and
    read-back expects another, this test fails in pytest.
    """
    captured: dict[str, object] = {}

    def _fake_insert(conn, **kwargs):
        # Fails loudly if the persist call site drops/renames ``output_text``
        # (the #215 ``raw_output`` regression).
        assert "output_text" in kwargs, "persist must pass output_text="
        captured["output_text"] = kwargs["output_text"]
        captured["output_type"] = kwargs["output_type"]
        captured["target_type"] = kwargs["target_type"]
        return 1

    # Empty fact bundle → the function returns a "line not found" payload and
    # skips the live Anthropic call, but we still want to assert persistence
    # semantics, so drive the supported-language synthesis path instead by
    # stubbing the seams it touches.
    from core.agent import fact_assembly as _fa

    class _Bundle:
        line_id = 7
        atf_text = "e2-gal"
        language = "Sumerian"
        dialect = None
        is_mixed_language = False
        language_shift_position = None
        language_supported = True
        missing_layers: list[str] = []
        context_variant = "a"

    monkeypatch.setattr(_fa, "assemble_line_facts", lambda conn, **kw: _Bundle())
    monkeypatch.setattr(
        agent_service.fact_assembly,
        "assemble_line_facts",
        lambda conn, **kw: _Bundle(),
    )

    class _FakeAnthropic:
        model = "claude-test"

    monkeypatch.setattr(agent_service, "_get_anthropic", lambda: _FakeAnthropic())

    # synthesize returns a result whose .text is parsed as JSON; an empty
    # object yields no suggestions (best-guess path) but still persists.
    class _Result:
        text = "{}"

    monkeypatch.setattr(
        agent_service, "synthesize_line_suggestion", lambda *a, **kw: _Result()
    )

    # First call: cache miss → persist.
    monkeypatch.setattr(
        agent_service.agent_outputs, "find_fresh", lambda conn, **kw: None
    )
    monkeypatch.setattr(agent_service.agent_outputs, "insert", _fake_insert)

    first = agent_service.do_suggest_line_translation(
        _FakeConn(),  # type: ignore[arg-type]
        p_number="P000001",
        surface_name="obverse",
        line_number="1",
        interaction_id_str="int-1",
    )

    # Persist happened with the right keyword and the right column shape.
    assert "output_text" in captured
    assert captured["output_type"] == "line_suggestion"
    persisted_text = captured["output_text"]
    assert isinstance(persisted_text, str)

    # The persisted JSON must carry the {"summary", "data"} envelope the
    # read-back path expects.
    decoded = json.loads(persisted_text)
    assert "summary" in decoded
    assert "data" in decoded

    # Now feed the captured text back through the read-back (cache-hit) path and
    # assert the payload survives the round-trip — same atf, same line_id.
    monkeypatch.setattr(
        agent_service.agent_outputs,
        "find_fresh",
        lambda conn, **kw: _persisted_from(persisted_text),
    )

    second = agent_service.do_suggest_line_translation(
        _FakeConn(),  # type: ignore[arg-type]
        p_number="P000001",
        surface_name="obverse",
        line_number="1",
        interaction_id_str="int-2",
    )

    assert second.data.atf == first.data.atf == "e2-gal"
    assert second.data.line_id == first.data.line_id == 7
    assert second.summary == first.summary
