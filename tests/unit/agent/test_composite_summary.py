"""Coverage for the composite-level AI summary (#168).

Pins the trust contract for ``do_summarize_composite`` without a database or a
live Anthropic call:

1. Cache hit: a persisted ``composite_summary`` is read back from
   ``output_text`` into a ``CardPayload`` with its citations intact.
2. Grounding failure: when synthesis cannot ground (``SynthesisGroundingError``),
   the response carries **no synthesis text** — never a fabricated paragraph —
   and is flagged as a degraded path. This is the load-bearing "no ungrounded
   claim" guarantee for a scholar-facing AI surface.
3. The persist call site writes ``output_type='composite_summary'`` /
   ``target_type='composite'`` (fails loudly if a keyword drifts, #215 class).
"""

from __future__ import annotations

from datetime import UTC, datetime

from api.services import agent_service
from core.agent.agent_outputs import PersistedOutput
from core.agent.citation_parser import SynthesisGroundingError
from core.agent.fact_assembly import CompositeFactBundle, Fact
from core.schemas.citation import Citation


class _FakeConn:
    """Stand-in for a psycopg connection; every DB seam is monkeypatched."""


def _bundle() -> CompositeFactBundle:
    b = CompositeFactBundle(q_number="Q000782", linked_count=72, exemplar_count=3851)
    b.facts = [
        Fact(
            n=1,
            text="composition Q-number: Q000782 (CDLI/ORACC catalog)",
            citation=Citation(
                n=1,
                source_kind="annotation_run",
                source_id="cdli_catalog",
                retrieval_field="designation",
            ),
        ),
        Fact(
            n=2,
            text="attestation: 72 witnesses linked (CDLI/ORACC catalog)",
            citation=Citation(
                n=2,
                source_kind="annotation_run",
                source_id="cdli_catalog",
                retrieval_field="exemplar_count",
            ),
        ),
    ]
    return b


def test_cache_hit_reads_back_grounded_summary(monkeypatch):
    """A persisted composite summary is returned with its synthesis + citations."""
    citation = Citation(
        n=2,
        source_kind="annotation_run",
        source_id="cdli_catalog",
        retrieval_field="exemplar_count",
    )
    persisted = PersistedOutput(
        id=1,
        interaction_id=None,
        output_type="composite_summary",
        target_type="composite",
        target_id="Q000782",
        focus=None,
        model="claude-test",
        prompt_version="composite-summary.v1",
        output_text="Attested by 72 witnesses [2].",
        citations=[citation],
        source_run_ids=[],
        best_guess_flag=False,
        generated_at=datetime.now(UTC),
    )

    monkeypatch.setattr(
        agent_service.fact_assembly,
        "assemble_composite_facts",
        lambda conn, q_number: _bundle(),
    )
    monkeypatch.setattr(
        agent_service.agent_outputs, "find_fresh", lambda conn, **kw: persisted
    )

    resp = agent_service.do_summarize_composite(
        _FakeConn(),  # type: ignore[arg-type]
        q_number="Q000782",
        interaction_id_int=None,
        interaction_id_str="int-1",
    )

    assert resp.data.synthesis == "Attested by 72 witnesses [2]."
    assert [c.n for c in resp.data.synthesis_citations] == [2]
    # No best-guess branch for composite summaries.
    assert resp.data.best_guess is None


def test_grounding_failure_yields_no_fabricated_summary(monkeypatch):
    """When synthesis cannot ground, the card has NO synthesis text (never a
    hallucinated paragraph) and the response is flagged degraded."""
    monkeypatch.setattr(
        agent_service.fact_assembly,
        "assemble_composite_facts",
        lambda conn, q_number: _bundle(),
    )
    monkeypatch.setattr(
        agent_service.agent_outputs, "find_fresh", lambda conn, **kw: None
    )

    def _raise(*a, **k):
        raise SynthesisGroundingError("unbound [9]", "draft text")

    monkeypatch.setattr(agent_service, "synthesize_composite_summary", _raise)

    class _Anthropic:
        model = "claude-test"

    monkeypatch.setattr(agent_service, "_get_anthropic", lambda: _Anthropic())

    resp = agent_service.do_summarize_composite(
        _FakeConn(),  # type: ignore[arg-type]
        q_number="Q000782",
        interaction_id_int=None,
        interaction_id_str="int-1",
    )

    # The trust guarantee: no fabricated synthesis on a grounding failure.
    assert resp.data.synthesis is None
    assert any(s.method == "degraded-no-synthesis" for s in resp.sources)


def test_persist_writes_composite_keywords(monkeypatch):
    """Cache miss persists with the composite output/target type (anti-drift)."""
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        agent_service.fact_assembly,
        "assemble_composite_facts",
        lambda conn, q_number: _bundle(),
    )
    monkeypatch.setattr(
        agent_service.agent_outputs, "find_fresh", lambda conn, **kw: None
    )

    class _Result:
        text = "Attested by 72 witnesses [2]."
        citations = [
            Citation(
                n=2,
                source_kind="annotation_run",
                source_id="cdli_catalog",
                retrieval_field="exemplar_count",
            )
        ]

    monkeypatch.setattr(
        agent_service, "synthesize_composite_summary", lambda *a, **k: _Result()
    )

    class _Anthropic:
        model = "claude-test"

    monkeypatch.setattr(agent_service, "_get_anthropic", lambda: _Anthropic())

    def _fake_insert(conn, **kwargs):
        captured.update(kwargs)
        return 1

    monkeypatch.setattr(agent_service.agent_outputs, "insert", _fake_insert)

    resp = agent_service.do_summarize_composite(
        _FakeConn(),  # type: ignore[arg-type]
        q_number="Q000782",
        interaction_id_int=None,
        interaction_id_str="int-1",
    )

    assert captured["output_type"] == "composite_summary"
    assert captured["target_type"] == "composite"
    assert captured["target_id"] == "Q000782"
    assert captured["best_guess_flag"] is False
    assert resp.data.synthesis == "Attested by 72 witnesses [2]."
