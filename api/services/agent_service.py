"""Agent service — orchestrates the three hero scenarios.

This service is the shared business logic that BOTH the REST routes (api/routes/search.py,
api/routes/agent.py) AND the MCP tools call. Same code path, two surfaces.

Public functions:
  do_search(...)              → ToolResponse[GroupedTablePayload]   (semantic_search)
  do_summarize_artifact(...)  → ToolResponse[CardPayload]           (summarize_artifact)
  do_interpret_token(...)     → ToolResponse[ChainPayload]          (interpret_token)
"""

from __future__ import annotations

import json
import logging
import re

import psycopg

from core.agent import agent_outputs, fact_assembly
from core.agent.anthropic_client import AnthropicClient
from core.agent.citation_parser import SynthesisGroundingError
from core.agent.fact_assembly import (
    ArtifactFactBundle,
    TokenFactBundle,
)
from core.agent.search_engine import SearchEngine
from core.agent.synthesis import (
    synthesize_artifact_summary,
    synthesize_line_suggestion,
    synthesize_token_interpretation,
)
from core.agent.voyage_client import VoyageClient
from core.schemas.citation import Citation
from core.schemas.envelope import (
    BestGuess,
    CardPayload,
    ChainPayload,
    ChainStep,
    Field,
    FollowUp,
    Group,
    GroupedTablePayload,
    Hypothesis,
    LineSuggestion,
    LineSuggestionPayload,
    TokenChainStep,
    ToolResponse,
)
from core.schemas.search import SearchParams
from core.schemas.sources import SourceRef

logger = logging.getLogger(__name__)

# Module-level singletons. Initialized lazily; tests can substitute via attribute.
_voyage: VoyageClient | None = None
_anthropic: AnthropicClient | None = None
_search_engine: SearchEngine | None = None

# First sentence: ends at ., !, or ? followed by space or end-of-string.
_re_sentence = re.compile(r"[^.!?]*[.!?](?=\s|$)")


def _get_voyage() -> VoyageClient | None:
    """Return Voyage client if configured, else None (semantic search degrades)."""
    global _voyage
    if _voyage is None:
        try:
            _voyage = VoyageClient()
        except RuntimeError as exc:
            logger.warning("Voyage unavailable: %s", exc)
            return None
    return _voyage


def _get_anthropic() -> AnthropicClient:
    global _anthropic
    if _anthropic is None:
        _anthropic = AnthropicClient()
    return _anthropic


def _get_search_engine() -> SearchEngine:
    global _search_engine
    if _search_engine is None:
        _search_engine = SearchEngine(voyage=_get_voyage())
    return _search_engine


# ── Helpers ───────────────────────────────────────────────────────────────────


def _source_refs_from_citations(citations: list[Citation]) -> list[SourceRef]:
    """Distill SourceRef list from a citation list (one entry per unique source)."""
    seen: set[tuple[str, str]] = set()
    refs: list[SourceRef] = []
    for c in citations:
        key = (c.source_kind, str(c.source_id))
        if key in seen:
            continue
        seen.add(key)
        label = c.publication_short or f"{c.source_kind}:{c.source_id}"
        refs.append(SourceRef(kind=c.source_kind, label=label))
    if not refs:
        refs.append(
            SourceRef.computed(method="grounded-synthesis", label="grounded synthesis")
        )
    return refs


def _source_run_ids(citations: list[Citation]) -> list[int]:
    return [c.annotation_run_id for c in citations if c.annotation_run_id is not None]


def _facts_to_fields(bundle: ArtifactFactBundle) -> list[Field]:
    """Render the structured fact list as Card fields. Renders even when
    synthesis is absent (degraded path)."""
    fields: list[Field] = []
    for f in bundle.facts:
        if f.text.startswith(
            "similar tablets"
        ) or f.citation.retrieval_field.startswith("similar_tablet"):
            continue  # similar-tablet entries are not catalog fields
        label, _, value = f.text.partition(":")
        ref = SourceRef(
            kind=f.citation.source_kind,
            label=f.citation.publication_short
            or f"{f.citation.source_kind}:{f.citation.source_id}",
        )
        fields.append(
            Field(
                label=label.strip().title(), value=value.strip() or None, sources=[ref]
            )
        )
    return fields


# ── 1. Search ────────────────────────────────────────────────────────────────


def do_search(
    conn: psycopg.Connection,
    params: SearchParams,
    interaction_id: str,
) -> ToolResponse[GroupedTablePayload]:
    """Hero scenario 1: semantic_search."""
    engine = _get_search_engine()
    results = engine.search(conn, params)

    types_requested = params.types or list(results.groups.keys())
    groups: list[Group] = []

    # Pre-fetch cached summaries for any tablet hits so we can show snippets.
    tablet_hits_all = results.groups.get("tablets", [])
    snippet_map: dict[str, str] = {}
    if tablet_hits_all:
        p_numbers = [h.p_number_ref for h in tablet_hits_all if h.p_number_ref]
        if p_numbers:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT ON (target_id) target_id, output_text
                    FROM agent_outputs
                    WHERE output_type = 'artifact_summary'
                      AND focus = 'general'
                      AND target_id = ANY(%s)
                    ORDER BY target_id, generated_at DESC
                    """,
                    (p_numbers,),
                )
                for row in cur.fetchall():
                    text = row["output_text"] or ""
                    m = _re_sentence.search(text)
                    snippet = (m.group(0) if m else text[:160]).strip()
                    snippet_map[row["target_id"]] = snippet

    for entity_type in types_requested:
        hits = results.groups.get(entity_type, [])
        total = results.totals.get(entity_type, 0)
        items = []
        for h in hits:
            item: dict = {
                "entity_id": h.entity_id,
                "primary_label": h.primary_label,
                "secondary_label": h.secondary_label,
                "score": round(h.score, 4),
                "p_number": h.p_number_ref,
                "sources": h.sources,
            }
            # Tablet-only display extras for the global-search drawer.
            if entity_type == "tablets":
                item["thumbnail_url"] = h.thumbnail_url
                item["pipeline_completeness"] = h.pipeline_completeness
                item["pipeline_stages"] = h.pipeline_stages
                if h.p_number_ref and h.p_number_ref in snippet_map:
                    item["snippet"] = snippet_map[h.p_number_ref]
            items.append(item)

        view_all = None
        if total > len(items):
            view_all = FollowUp(
                tool="semantic_search",
                args={
                    "q": params.q,
                    "types": [entity_type],
                    "limit": min(50, total),
                    "mode": params.mode,
                },
                label=f"View all {total} {entity_type}",
                rationale=f"Show every {entity_type} match for this query",
            )

        groups.append(
            Group(
                group_type=entity_type,
                items=items,
                total=total,
                cursor=None,  # cursor support is wired via decoded follow-up args
                view_all=view_all,
            )
        )

    populated = sum(1 for g in groups if g.items)
    summary = (
        f"{populated}/{len(groups)} entity types matched for '{params.q}'."
        if populated
        else f"No results found for '{params.q}'."
    )

    sources: list[SourceRef] = [
        SourceRef.computed(
            method="hybrid:lexical+semantic+rrf", label="hybrid retrieval"
        )
    ]
    follow_ups: list[FollowUp] = []
    if not populated:
        follow_ups.append(
            FollowUp(
                tool="semantic_search",
                args={"q": params.q, "mode": "lexical"},
                label="Retry as lexical-only",
                rationale="Try less aggressive matching",
            )
        )

    return ToolResponse[GroupedTablePayload](
        summary=summary,
        data=GroupedTablePayload(groups=groups),
        sources=sources,
        required_attributions=None,
        follow_ups=follow_ups,
        interaction_id=interaction_id,
        render_hint="table",
    )


# ── 2. Summarize artifact ────────────────────────────────────────────────────


def do_summarize_artifact(
    conn: psycopg.Connection,
    p_number: str,
    focus: str,
    interaction_id_int: int | None,
    interaction_id_str: str,
) -> ToolResponse[CardPayload]:
    """Hero scenario 2: summarize_artifact with lazy-persist."""
    prompt_version = "synthesis.v1"

    # 1. Lazy-load
    persisted = agent_outputs.find_fresh(
        conn,
        output_type="artifact_summary",
        target_type="artifact",
        target_id=p_number,
        focus=focus,
        prompt_version=prompt_version,
    )

    if persisted:
        return _card_response_from_persisted(
            conn,
            p_number,
            focus,
            persisted,
            interaction_id_str,
        )

    # 2. Assemble facts
    bundle = fact_assembly.assemble_artifact_facts(conn, p_number, focus=focus)
    if bundle is None:
        return _not_found_response(p_number, interaction_id_str)

    # 3. Synthesize
    anthropic = _get_anthropic()
    degraded_summary: str | None = None
    synthesis_text: str | None = None
    synthesis_citations: list[Citation] = []
    best_guess: BestGuess | None = None
    source_run_ids: list[int] = []

    try:
        result = synthesize_artifact_summary(
            anthropic, bundle, focus=focus, prompt_version=prompt_version
        )
        synthesis_text = result.text
        synthesis_citations = result.citations
        source_run_ids = _source_run_ids(synthesis_citations)
        best_guess = _extract_best_guess(synthesis_text, bundle)
    except SynthesisGroundingError as exc:
        logger.warning(
            "synthesis grounding failed for %s: %s", p_number, exc.last_complaint
        )
        degraded_summary = _degraded_summary_from_facts(bundle)

    # 4. Persist (skip on degraded path so we'll retry next time)
    if synthesis_text:
        try:
            agent_outputs.insert(
                conn,
                interaction_id=interaction_id_int,
                output_type="artifact_summary",
                target_type="artifact",
                target_id=p_number,
                focus=focus,
                model=anthropic.model,
                prompt_version=prompt_version,
                output_text=synthesis_text,
                citations=synthesis_citations,
                source_run_ids=source_run_ids,
                best_guess_flag=(best_guess is not None),
            )
        except Exception as exc:
            logger.warning("agent_outputs insert failed: %s", exc)

    # 5. Build CardPayload
    fields = _facts_to_fields(bundle)
    card = CardPayload(
        title=bundle.facts[0].text.replace("designation: ", "")
        if bundle.facts
        else p_number,
        subtitle=p_number,
        fields=fields,
        badges=_badges_from_bundle(bundle),
        synthesis=synthesis_text,
        synthesis_citations=synthesis_citations,
        best_guess=best_guess,
        language_supported=_language_supported(bundle),
    )

    summary = (
        degraded_summary
        or _plain_summary_from_synthesis(synthesis_text)
        or _degraded_summary_from_facts(bundle)
    )

    sources = _source_refs_from_citations(synthesis_citations)
    if not synthesis_text:
        sources.insert(
            0, SourceRef.computed(method="degraded-no-synthesis", label="degraded path")
        )

    return ToolResponse[CardPayload](
        summary=summary,
        data=card,
        sources=sources,
        required_attributions=None,
        follow_ups=_summarize_follow_ups(p_number, bundle),
        interaction_id=interaction_id_str,
        render_hint="card",
    )


def _card_response_from_persisted(
    conn: psycopg.Connection,
    p_number: str,
    focus: str,
    persisted: agent_outputs.PersistedOutput,
    interaction_id_str: str,
) -> ToolResponse[CardPayload]:
    bundle = fact_assembly.assemble_artifact_facts(conn, p_number, focus=focus)
    if bundle is None:
        bundle = ArtifactFactBundle(p_number=p_number)
    best_guess = (
        _extract_best_guess(persisted.output_text, bundle)
        if persisted.best_guess_flag
        else None
    )
    card = CardPayload(
        title=p_number,
        subtitle=focus,
        fields=_facts_to_fields(bundle),
        badges=_badges_from_bundle(bundle),
        synthesis=persisted.output_text,
        synthesis_citations=persisted.citations,
        best_guess=best_guess,
        language_supported=_language_supported(bundle),
    )
    return ToolResponse[CardPayload](
        summary=_plain_summary_from_synthesis(persisted.output_text) or p_number,
        data=card,
        sources=_source_refs_from_citations(persisted.citations),
        follow_ups=_summarize_follow_ups(p_number, bundle),
        interaction_id=interaction_id_str,
        render_hint="card",
    )


def _not_found_response(
    p_number: str, interaction_id_str: str
) -> ToolResponse[CardPayload]:
    return ToolResponse[CardPayload](
        summary=f"No artifact found for P-number {p_number}.",
        data=CardPayload(title=p_number, fields=[]),
        sources=[SourceRef.computed(method="lookup", label="not found")],
        interaction_id=interaction_id_str,
        render_hint="card",
    )


def _degraded_summary_from_facts(bundle: ArtifactFactBundle) -> str:
    """When synthesis fails, build a non-narrative summary from facts."""
    items = []
    for f in bundle.facts[:5]:
        items.append(f.text)
    return "Summary unavailable; key facts: " + "; ".join(items) + "."


def _plain_summary_from_synthesis(text: str | None) -> str | None:
    if not text:
        return None
    # Strip [n] markers for the plain summary field
    return re.sub(r"\s*\[\d+\]", "", text).strip()


_HYPOTHESIS_SENTENCE_RE = re.compile(r"\(hypothesis\)([^.!?]*[.!?])", re.I)


def _extract_best_guess(
    text: str | None, bundle: ArtifactFactBundle
) -> BestGuess | None:
    if not text:
        return None
    m = _HYPOTHESIS_SENTENCE_RE.search(text)
    if not m:
        return None
    hypothesis_text = m.group(0).strip()
    # Pull citations from the hypothesis sentence
    cited_ns = [int(x) for x in re.findall(r"\[(\d+)\]", hypothesis_text)]
    fact_by_n = {f.n: f for f in bundle.facts}
    citations = [fact_by_n[n].citation for n in cited_ns if n in fact_by_n]
    similar_p = [st.p_number for st in bundle.similar_tablets if st.n in cited_ns]
    return BestGuess(
        hypothesis=hypothesis_text,
        confidence_band="medium" if len(cited_ns) >= 3 else "low",
        evidence_chain=[f.text for f in bundle.facts if f.n in cited_ns][:4],
        similar_tablets=similar_p,
        citations=citations,
    )


def _language_supported(bundle: ArtifactFactBundle) -> bool:
    """Sumerian and Akkadian (all dialects) are in scope for AI suggestions."""
    for f in bundle.facts:
        if f.text.startswith("primary language:"):
            lang = f.text.split(":", 1)[1].strip().lower()
            return lang.startswith("sumerian") or lang.startswith("akkadian")
    return True  # unknown language → allow rather than silently block


def _badges_from_bundle(bundle: ArtifactFactBundle) -> list:
    badges = []
    for f in bundle.facts:
        if f.text.startswith("period:"):
            badges.append({"label": f.text.split(":", 1)[1].strip(), "kind": "period"})
        elif f.text.startswith("provenience:"):
            badges.append(
                {"label": f.text.split(":", 1)[1].strip(), "kind": "provenience"}
            )
        elif f.text.startswith("pipeline completeness:"):
            score = f.text.split(":", 1)[1].split("/", 1)[0].strip()
            badges.append({"label": f"completeness {score}/5", "kind": "completeness"})
    return badges


def _summarize_follow_ups(p_number: str, bundle: ArtifactFactBundle) -> list[FollowUp]:
    follow_ups: list[FollowUp] = []
    if bundle.similar_tablets:
        first = bundle.similar_tablets[0]
        follow_ups.append(
            FollowUp(
                tool="summarize_artifact",
                args={"p_number": first.p_number, "focus": "general"},
                label=f"Summarize similar tablet {first.p_number}",
                rationale=f"Cosine {first.cosine:.2f} — same period/provenience pattern",
            )
        )
    follow_ups.append(
        FollowUp(
            tool="semantic_search",
            args={"q": p_number, "types": ["tablets"]},
            label="Search related tablets",
        )
    )
    return follow_ups


# ── 3. Interpret token ───────────────────────────────────────────────────────


def do_interpret_token(
    conn: psycopg.Connection,
    p_number: str,
    token_id: int,
    interaction_id_int: int | None,
    interaction_id_str: str,
) -> ToolResponse[ChainPayload]:
    """Hero scenario 3: interpret_token with lazy-persist."""
    prompt_version = "interpret-token.v1"
    target_id = str(token_id)

    persisted = agent_outputs.find_fresh(
        conn,
        output_type="token_interpretation",
        target_type="token",
        target_id=target_id,
        focus=None,
        prompt_version=prompt_version,
    )
    if persisted:
        chain = _chain_from_persisted_text(persisted.output_text, persisted.citations)
        return ToolResponse[ChainPayload](
            summary=chain[0]
            if isinstance(chain, tuple)
            else "Cached token interpretation.",
            data=chain[1] if isinstance(chain, tuple) else chain,
            sources=_source_refs_from_citations(persisted.citations),
            interaction_id=interaction_id_str,
            render_hint="chain",
        )

    bundle = fact_assembly.assemble_token_facts(conn, p_number, token_id)
    if bundle is None:
        return ToolResponse[ChainPayload](
            summary=f"Token {token_id} not found on artifact {p_number}.",
            data=ChainPayload(steps=[]),
            sources=[SourceRef.computed(method="lookup", label="not found")],
            interaction_id=interaction_id_str,
            render_hint="chain",
        )

    anthropic = _get_anthropic()
    try:
        result = synthesize_token_interpretation(
            anthropic, bundle, prompt_version=prompt_version
        )
        summary_text, chain_payload = _parse_token_synthesis_json(
            result.text, bundle, result.citations
        )
        source_run_ids = _source_run_ids(result.citations)

        try:
            agent_outputs.insert(
                conn,
                interaction_id=interaction_id_int,
                output_type="token_interpretation",
                target_type="token",
                target_id=target_id,
                focus=None,
                model=anthropic.model,
                prompt_version=prompt_version,
                output_text=result.text,
                citations=result.citations,
                source_run_ids=source_run_ids,
                best_guess_flag=bool(chain_payload.hypotheses),
            )
        except Exception as exc:
            logger.warning("agent_outputs insert failed: %s", exc)

        return ToolResponse[ChainPayload](
            summary=summary_text,
            data=chain_payload,
            sources=_source_refs_from_citations(result.citations),
            interaction_id=interaction_id_str,
            render_hint="chain",
        )
    except SynthesisGroundingError as exc:
        logger.warning("token interpretation grounding failed: %s", exc.last_complaint)
        return _degraded_token_response(bundle, interaction_id_str)


def _parse_token_synthesis_json(
    text: str,
    bundle: TokenFactBundle,
    citations: list[Citation],
) -> tuple[str, ChainPayload]:
    """Parse the JSON-formatted interpret-token output into a ChainPayload."""
    fact_by_n = {f.n: f for f in bundle.facts}

    # Best-effort JSON parse — accept either pure JSON or JSON-in-text
    try:
        json_str = _extract_first_json_object(text)
        data = json.loads(json_str)
    except Exception:
        # Fall back to a minimal chain from the bundle
        return _bundle_to_chain(bundle, citations)

    summary = data.get("summary") or ""
    steps_raw = data.get("steps", [])
    hypotheses_raw = data.get("hypotheses") or []

    steps: list[ChainStep] = []
    for s in steps_raw:
        ns = s.get("fact_refs") or []
        step_citations = [fact_by_n[int(n)].citation for n in ns if int(n) in fact_by_n]
        steps.append(
            ChainStep(
                label=s.get("label") or "",
                value=str(s.get("value") or ""),
                sources=[
                    SourceRef(
                        kind=c.source_kind,
                        label=c.publication_short or f"{c.source_kind}:{c.source_id}",
                    )
                    for c in step_citations
                ],
            )
        )

    hypotheses: list[Hypothesis] = []
    for h in hypotheses_raw:
        ns = h.get("fact_refs") or []
        h_citations = [fact_by_n[int(n)].citation for n in ns if int(n) in fact_by_n]
        hypotheses.append(
            Hypothesis(
                reading=str(h.get("reading") or "the candidate reading (unspecified)"),
                confidence_band=h.get("confidence_band") or "low",
                evidence_chain=list(h.get("evidence_chain") or []),
                citations=h_citations,
            )
        )

    return summary, ChainPayload(steps=steps, hypotheses=hypotheses or None)


def _bundle_to_chain(
    bundle: TokenFactBundle, citations: list[Citation]
) -> tuple[str, ChainPayload]:
    """Fallback: render the bundle as a chain when synthesis JSON is unparsable."""
    steps = []
    for f in bundle.facts[:10]:
        steps.append(
            ChainStep(
                label=f.text.split(":", 1)[0].title(),
                value=f.text.split(":", 1)[1].strip() if ":" in f.text else f.text,
                sources=[
                    SourceRef(
                        kind=f.citation.source_kind,
                        label=f.citation.publication_short
                        or f"{f.citation.source_kind}:{f.citation.source_id}",
                    )
                ],
            )
        )
    return (
        "Token facts (synthesis fallback).",
        ChainPayload(steps=steps, hypotheses=None),
    )


def _chain_from_persisted_text(text: str, citations: list[Citation]) -> ChainPayload:
    """Reconstruct a ChainPayload from a persisted output_text."""
    try:
        data = json.loads(_extract_first_json_object(text))
    except Exception:
        return ChainPayload(steps=[], hypotheses=None)
    steps_raw = data.get("steps", [])
    steps = [
        ChainStep(
            label=s.get("label") or "", value=str(s.get("value") or ""), sources=[]
        )
        for s in steps_raw
    ]
    hypotheses_raw = data.get("hypotheses") or []
    hypotheses = [
        Hypothesis(
            reading=str(h.get("reading") or "the candidate reading"),
            confidence_band=h.get("confidence_band") or "low",
            evidence_chain=list(h.get("evidence_chain") or []),
            citations=[],
        )
        for h in hypotheses_raw
    ]
    return ChainPayload(steps=steps, hypotheses=hypotheses or None)


def _extract_first_json_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in text")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise ValueError("unbalanced JSON")


def _degraded_token_response(
    bundle: TokenFactBundle, interaction_id_str: str
) -> ToolResponse[ChainPayload]:
    summary, payload = _bundle_to_chain(bundle, [])
    return ToolResponse[ChainPayload](
        summary=summary,
        data=payload,
        sources=[
            SourceRef.computed(method="degraded-no-synthesis", label="degraded path")
        ],
        interaction_id=interaction_id_str,
        render_hint="chain",
    )


# ── 4. Suggest line translation ───────────────────────────────────────────────


def do_suggest_line_translation(
    conn: psycopg.Connection,
    *,
    p_number: str,
    surface_name: str,
    line_number: str,
    session_variant: str | None = None,
    interaction_id_str: str,
) -> ToolResponse[LineSuggestionPayload]:
    """Hero scenario 4: suggest_line_translation.

    Returns ranked translation proposals for a single cuneiform line,
    with per-token confidence chain and missing-layer diagnostics.
    """
    prompt_version = "suggest-line.v1"

    bundle = fact_assembly.assemble_line_facts(
        conn,
        p_number=p_number,
        surface_name=surface_name,
        line_number=line_number,
        session_variant=session_variant,
    )

    if bundle is None:
        empty_payload = LineSuggestionPayload(
            atf="",
            language="Unknown",
            language_supported=False,
            missing_layers=["Line not found in database"],
            model="",
            prompt_version=prompt_version,
        )
        return ToolResponse[LineSuggestionPayload](
            summary=f"Line {line_number} not found on {surface_name} of {p_number}.",
            data=empty_payload,
            sources=[SourceRef.computed(method="line-not-found", label="not found")],
            interaction_id=interaction_id_str,
            render_hint="chain",
        )

    if not bundle.language_supported:
        unsupported_payload = LineSuggestionPayload(
            line_id=bundle.line_id,
            atf=bundle.atf_text,
            language=bundle.language,
            language_supported=False,
            missing_layers=bundle.missing_layers,
            model="",
            prompt_version=prompt_version,
        )
        return ToolResponse[LineSuggestionPayload](
            summary=f"AI suggestions not available for {bundle.language}.",
            data=unsupported_payload,
            sources=[
                SourceRef.computed(
                    method="language-not-supported", label="unsupported language"
                )
            ],
            interaction_id=interaction_id_str,
            render_hint="chain",
        )

    anthropic = _get_anthropic()

    try:
        result = synthesize_line_suggestion(
            anthropic, bundle, prompt_version=prompt_version
        )
        raw_json = result.text.strip()
    except SynthesisGroundingError as exc:
        logger.warning(
            "line synthesis grounding failed for %s %s %s: %s",
            p_number,
            surface_name,
            line_number,
            exc.last_complaint,
        )
        raw_json = None

    # Parse JSON output
    token_chain: list[TokenChainStep] = []
    suggestions: list[LineSuggestion] = []

    if raw_json:
        try:
            import json as _json  # noqa: PLC0415

            parsed = _json.loads(raw_json)
            for step in parsed.get("token_chain", []):
                token_chain.append(
                    TokenChainStep(
                        token_id=int(step.get("token_id", 0)),
                        raw_form=step.get("raw_form", ""),
                        is_determinative=bool(step.get("is_determinative", False)),
                        lemma=step.get("lemma"),
                        guide_word=step.get("guide_word"),
                        pos=step.get("pos"),
                        case=step.get("case"),
                        number=step.get("number"),
                        gender=step.get("gender"),
                        translation_fragment=step.get("translation_fragment"),
                        fact_refs=step.get("fact_refs", []),
                        confidence_band=step.get("confidence_band", "unknown"),
                    )
                )
            for sug in parsed.get("suggestions", []):
                suggestions.append(
                    LineSuggestion(
                        rank=int(sug.get("rank", 1)),
                        translation=sug.get("translation", ""),
                        confidence_band=sug.get("confidence_band", "low"),
                        evidence_chain=sug.get("evidence_chain", []),
                        fact_refs=sug.get("fact_refs", []),
                        caveat=sug.get("caveat"),
                    )
                )
        except Exception as exc:
            logger.warning("line suggestion JSON parse failed: %s", exc)

    model_name = anthropic.model if hasattr(anthropic, "model") else ""

    payload = LineSuggestionPayload(
        line_id=bundle.line_id,
        atf=bundle.atf_text,
        language=bundle.language,
        dialect=bundle.dialect,
        is_mixed_language=bundle.is_mixed_language,
        language_shift_position=bundle.language_shift_position,
        language_supported=bundle.language_supported,
        token_chain=token_chain,
        suggestions=suggestions,
        missing_layers=bundle.missing_layers,
        context_variant=bundle.context_variant,
        model=model_name,
        prompt_version=prompt_version,
    )

    top_suggestion = (
        suggestions[0].translation if suggestions else "No suggestion generated"
    )
    summary = f"Line {line_number}: {top_suggestion}"

    return ToolResponse[LineSuggestionPayload](
        summary=summary,
        data=payload,
        sources=[
            SourceRef.computed(method="grounded-synthesis", label="grounded synthesis")
        ],
        interaction_id=interaction_id_str,
        render_hint="chain",
    )
