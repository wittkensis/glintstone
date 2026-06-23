"""The ToolResponse envelope — every agentic surface returns this shape.

See `.claude/skills/gs-expert-agentic/envelope.md` for the full contract.

Why generic over T: each tool's `data` payload is typed (Table | Card | Chain | …).
Clients that render JSON inspect `render_hint` to pick the rendering. Plain-text
clients fall back to `summary`.
"""

from datetime import datetime, timezone
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field as PField

from core.schemas.citation import Citation
from core.schemas.sources import Attribution, SourceRef

RenderHint = Literal["table", "card", "chain", "timeline", "map", "list"]


# ── FollowUp ──────────────────────────────────────────────────────────────────


class FollowUp(BaseModel):
    """A suggested next tool call — first-class, not a hyperlink.

    Claude Desktop renders these as clickable chips with the args pre-filled;
    the web debug UI as buttons; the agent reads them as candidate next moves.
    """

    tool: str = PField(description="Tool name — e.g. 'semantic_search', 'walk_token'")
    args: dict = PField(default_factory=dict, description="Fully-typed pre-filled args")
    label: str = PField(description="Human-readable button text")
    rationale: str | None = PField(
        default=None, description="One sentence on why this follow-up is useful"
    )


# ── Payload variants (Table, Card, Chain, Timeline, Map, List) ────────────────


# Table


class Group(BaseModel):
    group_type: str = PField(description="'tablets' | 'lemmas' | 'scholars' | ...")
    items: list[dict] = PField(default_factory=list, description="Up to `limit` rows")
    total: int = 0
    cursor: str | None = None
    view_all: FollowUp | None = None


class GroupedTablePayload(BaseModel):
    """For semantic_search and other multi-entity-type results."""

    groups: list[Group] = PField(default_factory=list)


class TablePayload(BaseModel):
    """For single-type, flat tables (find_attestations etc.)."""

    columns: list[str]
    rows: list[list]
    total: int = 0
    cursor: str | None = None
    facets: dict[str, dict] = PField(
        default_factory=dict,
        description="{facet_name: {value: count}} for client-side filter UI",
    )


# Card


class Field(BaseModel):
    label: str
    value: str | int | float | None
    sources: list[SourceRef] = PField(default_factory=list)


class Badge(BaseModel):
    label: str
    kind: (
        Literal["period", "language", "genre", "provenience", "completeness", "status"]
        | None
    ) = None


class BestGuess(BaseModel):
    """Only present when pipeline_completeness ≤ 2 AND ≥3 similar tablets above threshold."""

    hypothesis: str = PField(
        description="Must use 'resembles' / 'consistent with' / 'looks like'"
    )
    confidence_band: Literal["low", "medium", "high"]
    evidence_chain: list[str]
    similar_tablets: list[str] = PField(
        default_factory=list, description="P-numbers used as priors"
    )
    citations: list[Citation] = PField(default_factory=list)


class CardPayload(BaseModel):
    title: str
    subtitle: str | None = None
    fields: list[Field] = PField(default_factory=list)
    badges: list[Badge] = PField(default_factory=list)
    image_url: str | None = None
    synthesis: str | None = PField(
        default=None,
        description="Grounded narrative with [n] markers; bound to synthesis_citations",
    )
    synthesis_citations: list[Citation] = PField(default_factory=list)
    best_guess: BestGuess | None = None
    model: str = PField(
        default="",
        description="Model id that authored the synthesis (e.g. 'claude-sonnet'); surfaced in the AI meta line for provenance",
    )
    language_supported: bool = PField(
        default=True,
        description="False when the primary language is outside the AI-suggestion scope (non-Sumerian/Akkadian)",
    )


# Chain


class Hypothesis(BaseModel):
    """For interpret_token when a token lacks a lemmatization pipeline."""

    reading: str = PField(
        description=(
            "Must start with 'the candidate reading', 'resembles', "
            "'consistent with', or 'may correspond to'"
        )
    )
    confidence_band: Literal["low", "medium", "high"]
    evidence_chain: list[str] = PField(
        description="1-4 short fragments describing the inference"
    )
    citations: list[Citation] = PField(default_factory=list)


class ChainStep(BaseModel):
    label: str = PField(
        description="'Written form' | 'Normalization' | 'Lemma' | 'Sense' | ..."
    )
    value: str
    sources: list[SourceRef] = PField(default_factory=list)
    confidence: float | None = PField(
        default=None,
        description="0..1; absent when the step is factual (not hypothetical)",
    )


class ChainPayload(BaseModel):
    steps: list[ChainStep]
    hypotheses: list[Hypothesis] | None = PField(
        default=None,
        description="None when the chain is complete; populated for interpret_token edge cases",
    )


# Line Translation Suggestions


class TokenChainStep(BaseModel):
    token_id: int
    raw_form: str
    is_determinative: bool = False
    lemma: str | None = None
    guide_word: str | None = None
    pos: str | None = None
    case: str | None = None
    number: str | None = None
    gender: str | None = None
    translation_fragment: str | None = PField(
        default=None,
        description="null when confidence_band is 'unknown' — prevent hallucination",
    )
    fact_refs: list[int] = PField(default_factory=list)
    confidence_band: Literal["known", "inferred", "unknown"] = "unknown"


class LineSuggestion(BaseModel):
    rank: int
    translation: str
    confidence_band: Literal["low", "medium", "high"]
    evidence_chain: list[str] = PField(
        default_factory=list,
        description="1-4 short fragments explaining the reasoning",
    )
    fact_refs: list[int] = PField(default_factory=list)
    caveat: str | None = None


class LineSuggestionPayload(BaseModel):
    line_id: int | None = None
    atf: str
    language: str
    dialect: str | None = None
    is_mixed_language: bool = False
    language_shift_position: int | None = None
    language_supported: bool = True
    token_chain: list[TokenChainStep] = PField(default_factory=list)
    suggestions: list[LineSuggestion] = PField(default_factory=list)
    missing_layers: list[str] = PField(
        default_factory=list,
        description="Server-computed list of missing pipeline stages affecting confidence",
    )
    context_variant: Literal["a", "b"] = "a"
    model: str = ""
    prompt_version: str = ""


# Timeline


class TimelineEvent(BaseModel):
    date: str | None = PField(default=None, description="ISO 8601 or BCE marker")
    label: str
    description: str | None = None
    sources: list[SourceRef] = PField(default_factory=list)


class TimelinePayload(BaseModel):
    events: list[TimelineEvent]


# Map


class MapPoint(BaseModel):
    coords: tuple[float, float] = PField(description="(lat, lon)")
    label: str
    p_number: str | None = None
    sources: list[SourceRef] = PField(default_factory=list)


class MapPayload(BaseModel):
    points: list[MapPoint]


# List


class ListPayload(BaseModel):
    items: list[dict]
    cursor: str | None = None
    total: int = 0


# ── ToolResponse[T] ───────────────────────────────────────────────────────────


T = TypeVar("T")


class ToolResponse(BaseModel, Generic[T]):
    """The contract every agentic surface honors.

    `sources` is never empty — for embedding-only results, attach
    `SourceRef.computed(method='voyage-3-large/cosine')`.

    `interaction_id` is the binding key to `agent_interactions` for the
    learning loop (see learning-loop.md).
    """

    summary: str = PField(
        description="One-paragraph human read; no [n] markers in this field"
    )
    data: T
    sources: list[SourceRef] = PField(
        default_factory=list,
        description="ALWAYS populated (never []); use SourceRef.computed() as fallback",
    )
    required_attributions: list[Attribution] | None = None
    follow_ups: list[FollowUp] = PField(default_factory=list)
    interaction_id: str
    render_hint: RenderHint
    generated_at: datetime = PField(default_factory=lambda: datetime.now(timezone.utc))
