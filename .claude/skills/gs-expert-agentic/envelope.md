---
question: "What does every tool response look like, what payload shapes are valid, and how does View-All work?"
created: 2026-05-12
modified: 2026-05-12
context: "Owns the ToolResponse envelope used by every REST route and every MCP tool. The single rendering contract clients depend on."
status: active
audience: [claude, engineers]
owners: [eric]
related_issues: []
related_skills: [gs-expert-agentic]
supersedes: null
superseded_by: null
---

# Response envelope

Every agentic surface (MCP tool, REST route under `/search` or `/agent`) returns the same outer shape. Clients that can render JSON (Claude Desktop, web app, debug UI) inspect `data`. Plain-text clients fall back to `summary`.

## Shape

```python
class ToolResponse(BaseModel, Generic[T]):
    summary: str                          # one-paragraph human read; no citation markers
    data: T                                # payload — typed by render_hint
    sources: list[SourceRef]               # always populated (never [])
    required_attributions: list[Attribution] | None = None
    follow_ups: list[FollowUp] = []        # suggested next tool calls with prefilled args
    interaction_id: str                    # binds this response to a row in agent_interactions
    render_hint: RenderHint                # "table" | "card" | "chain" | "timeline" | "map" | "list"
    generated_at: datetime                 # server time, UTC
```

`sources[]` is never empty. If a tool truly has nothing to cite (e.g. an embedding-only nearest-neighbor probe), it emits a `SourceRef(kind="computed", method="voyage-3-large/cosine")` row.

## Payload variants by render_hint

| `render_hint` | Pydantic class | Used by |
|---|---|---|
| `table` | `TablePayload` | `semantic_search`, `find_attestations` |
| `card` | `CardPayload` | `find_artifact`, `lookup_lemma`, `summarize_artifact` |
| `chain` | `ChainPayload` | `walk_token`, `interpret_token` |
| `timeline` | `TimelinePayload` | annotation history |
| `map` | `MapPayload` | provenience-aware queries |
| `list` | `ListPayload` | scrollable results |

### TablePayload (grouped, with View-All)

```python
class GroupedTablePayload(BaseModel):
    groups: list[Group]

class Group(BaseModel):
    group_type: str                       # "tablets" | "lemmas" | "scholars" | ...
    items: list[dict]                     # up to limit (default 5)
    total: int                            # total matching, for the View-All affordance
    cursor: str | None                    # opaque; encodes score + tiebreaker id
    view_all: FollowUp | None             # filled when total > limit
```

When `types=[single]` AND `limit > 5`, response collapses to a flat `TablePayload` with `rows`, `columns`, `facets`, `total`, `cursor`. Same client rendering, no special case.

### ChainPayload

```python
class ChainPayload(BaseModel):
    steps: list[ChainStep]
    hypotheses: list[Hypothesis] | None   # for interpret_token; absent for walk_token

class ChainStep(BaseModel):
    label: str                            # "Written form" | "Normalization" | "Lemma" | ...
    value: str
    sources: list[SourceRef]
    confidence: float | None              # 0..1; absent when factual not hypothetical
```

### CardPayload

```python
class CardPayload(BaseModel):
    title: str
    subtitle: str | None
    fields: list[Field]                   # label/value pairs with per-field sources
    badges: list[Badge] = []              # period, language, genre, etc.
    image_url: str | None
    synthesis: str | None                 # grounded narrative; contains [n] markers
    synthesis_citations: list[Citation] | None  # bound to [n] markers in synthesis
    best_guess: BestGuess | None          # only present when completeness ≤ 2

class Field(BaseModel):
    label: str
    value: str | int | float | None
    sources: list[SourceRef]              # never empty when value is non-null

class BestGuess(BaseModel):
    hypothesis: str
    confidence_band: Literal["low", "medium", "high"]
    evidence_chain: list[str]             # human-readable, e.g. "Drehem provenience + sila3 measure"
    similar_tablets: list[str]            # p_numbers used as priors
    citations: list[Citation]
```

## View-All flow

```jsonc
{
  "groups": [
    {
      "group_type": "tablets",
      "items": [ /* 5 */ ],
      "total": 247,
      "cursor": "eyJzY29yZSI6Li4ufQ",
      "view_all": {
        "tool": "semantic_search",
        "args": {
          "q": "harvest reports Nippur silver",
          "types": ["tablets"],
          "limit": 50,
          "cursor": "eyJzY29yZSI6Li4ufQ"
        },
        "label": "View all 247 tablets"
      }
    }
  ]
}
```

- **Cursor TTL: 5 minutes.** Same as Anthropic prompt cache, same as Voyage query embedding cache. After expiry the agent re-embeds; this is a few ms.
- Cursor encodes `(score, id)` so pagination is stable across calls; we cache the query embedding by `sha256(q)` for the TTL window.
- A group with `total ≤ limit` has `cursor: null, view_all: null` — client shouldn't render an expand affordance.

## FollowUp shape

```python
class FollowUp(BaseModel):
    tool: str                             # name of another tool the agent can call
    args: dict                            # pre-filled, fully-typed
    label: str                            # human-readable button text
    rationale: str | None                 # one sentence why this is a useful next step
```

FollowUps are **first-class suggestions**, not hyperlinks. Claude Desktop renders them as clickable chips; web app renders them as buttons; the agent reads them as candidate next moves.

## RenderHint enum freeze

This list is a **public contract**. We can add values, never remove or repurpose.

v1: `table` | `card` | `chain` | `timeline` | `map` | `list`

Adding a new hint requires a `decisions.md` entry and a same-commit bump to this file.

## Litmus test (the rendering contract is correct iff)

1. `semantic_search("gilgamesh")` → `ToolResponse[GroupedTablePayload]` with at least 2 non-empty groups, every group has `total` + `cursor` filled.
2. `summarize_artifact("P227657")` → `ToolResponse[CardPayload]` with `synthesis` non-empty, `synthesis_citations` covering every `[n]` in synthesis.
3. `interpret_token(...)` for an unlemmatized token → `ToolResponse[ChainPayload]` with `hypotheses` populated, every hypothesis has `confidence_band` and `evidence_chain`.
4. Round-trip through `model_dump_json()` and `model_validate_json()` preserves every field including `cursor`.
