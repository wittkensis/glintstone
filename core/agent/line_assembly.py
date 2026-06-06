"""Intermediate payload for line-translation fact assembly.

This dataclass is the contract between assemble_line_facts() in fact_assembly.py
and the synthesis layer. It is NOT the API envelope (that is
core.schemas.envelope.LineSuggestionPayload). This is the internal assembler
output — plain data with no Pydantic overhead.

Why a separate module: keeping it here avoids a circular import between
fact_assembly and synthesis, and makes the boundary between data-collection
and rendering explicit.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LineSuggestionPayload:
    """Assembled context for a single-line translation suggestion.

    Produced by assemble_line_facts() (fact_assembly.py).
    Consumed by synthesize_line_suggestion() (synthesis.py).

    The existing LineFactBundle in fact_assembly.py carries this same data
    via the Fact list + token_rows + missing_layers fields. This dataclass
    offers a lighter alternative for callers that want direct field access
    without iterating the Fact list. The two can coexist — LineFactBundle
    is the richer form used by the synthesis loop; this class is available
    for simpler callers or future routes that bypass the full fact list.
    """

    p_number: str
    line_id: int | None

    # Core line identity
    line_atf: str  # raw ATF text of the target line
    surface_type: str  # e.g. "obverse", "reverse", "left edge"

    # Preceding context — up to 3 lines before the target, in order
    preceding_lines: list[str] = field(default_factory=list)

    # Token-level lemma data for this line, ordered by token position
    # Each dict: {form: str, citation_form: str|None, guide_word: str|None}
    line_lemmas: list[dict] = field(default_factory=list)

    # Genre × period vocabulary priors from the genre_period_lemma_prior view.
    # Top 20 by rank. Empty list when the view is absent (migration 043 pending)
    # or when genre/period metadata is missing.
    # Each dict: {citation_form: str, guide_word: str|None, rank: int}
    genre_priors: list[dict] = field(default_factory=list)

    # Artifact-level metadata (denormalised here for prompt rendering convenience)
    artifact_language: str = ""
    artifact_genre: str = ""
    artifact_period: str = ""

    # Prompt version to use when this payload is rendered into a prompt
    prompt_version: str = "suggest-line.v1"
