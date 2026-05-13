---
question: "How does grounded synthesis cite sources, what's the reject-retry rule, and how will future academic citation styles plug in?"
created: 2026-05-12
modified: 2026-05-12
context: "Owns the own-rolled citation contract used by summarize_artifact and interpret_token. Decided against Anthropic's Citations API to stay model-agnostic. Future CSL/BibTeX rendering is planned but out of scope for v1."
status: active
audience: [claude, engineers]
owners: [eric]
related_issues: []
related_skills: [gs-expert-agentic]
supersedes: null
superseded_by: null
---

# Citation contract

Grounded synthesis is the core of `summarize_artifact` and `interpret_token`. Both call Claude with a structured fact list and require every claim to cite back to a source ID. This file is the contract.

## The internal `Citation` object

Lives in `core/schemas/citation.py`. **Components decomposed**, not pre-formatted strings — so any future academic style can render the same data.

```python
class Citation(BaseModel):
    n: int                                     # the [n] marker in synthesis text
    source_kind: Literal[
        "annotation_run",                      # a run in annotation_runs
        "publication",                         # a row in publications
        "authority_link",                      # external (Wikidata, VIAF, Pleiades…)
        "computed",                            # derived (e.g. "5 similar tablets by cosine ≥ 0.78")
        "lexical_lemma",                       # direct lemma reference
        "named_entity",                        # entity from named_entities
    ]
    source_id: int | str                       # primary key of the source row
    scholar_id: int | None = None              # scholars.id when applicable
    scholar_name: str | None = None            # denormalized for display
    year: int | None = None                    # publication year
    publication_short: str | None = None       # "Parpola 1987" — what most renderings need
    publication_ref: str | None = None         # full title
    page_ref: str | None = None                # e.g. "pp. 12-14" or "no. 47"
    url: str | None = None
    retrieval_field: str                       # what the citation supports — "period" | "lemma:8841" | "similar_tablet:P227657"
    annotation_run_id: int | None = None       # always populated when source_kind in {"annotation_run", "lexical_lemma", "named_entity"}
```

`retrieval_field` is the audit channel. It tells you *why* the LLM cited this row, which lets us spot hallucination (citation present but content unrelated).

## The synthesis loop

```
1. Caller calls assemble_facts(target) → list[Fact]
       Fact = {n: int, text: str, citation: Citation}

2. Caller calls synthesize(facts, system_prompt, user_intent)
   → Claude returns text with [n] markers

3. Validator parses [n] markers:
   - Every marker n must exist in the Fact list
   - Sentences without any marker that make non-trivial claims fail
   - First failure → one retry with the validator's complaint appended
   - Second failure → raise SynthesisGroundingError

4. Caller assembles ToolResponse:
   - synthesis: str  (text with markers intact)
   - synthesis_citations: list[Citation]  (filtered to those actually cited)
   - sources: list[SourceRef]  (derived from synthesis_citations + structured facts)
```

The numbered fact list pattern is what makes this model-agnostic. Any model that can read "Fact [3]: period is Ur III" and write "the tablet is Ur III in date [3]" passes the contract.

## System prompt anchors

Every synthesis system prompt **must** contain these clauses (verbatim or paraphrased — they're load-bearing). Locked here so prompt tweaks don't accidentally drop one.

1. *"You are grounding a scholarly summary. Every factual claim must be supported by a `[n]` marker referring to a fact in the FACTS list."*
2. *"Do not state any fact that is not in the FACTS list. If you cannot support a claim with a fact, omit the claim."*
3. *"`[n]` markers go immediately after the claim they support, before the period: `The tablet is Ur III [3].`"*
4. *"When a claim is supported by multiple facts, cite all of them: `mentions the king Šulgi [7][9]`."*
5. *"For hypothetical or best-guess content, mark it with `(hypothesis)` and still cite the supporting facts. Phrase as resemblance, never as fact: 'resembles X', not 'is X'."*

The synthesis prompt files in [prompts/](prompts/) embed these.

## Reject-retry rule

```python
def validate_synthesis(text: str, facts: list[Fact]) -> ValidationResult:
    valid_ns = {f.n for f in facts}
    markers = re.findall(r"\[(\d+)\]", text)
    unknown_ns = {int(m) for m in markers} - valid_ns

    if unknown_ns:
        return ValidationResult(
            ok=False,
            complaint=f"You cited [{','.join(map(str, sorted(unknown_ns)))}] but those numbers are not in the FACTS list. Only cite numbers shown in FACTS."
        )

    sentences = split_sentences(text)
    uncited_factual = [s for s in sentences if is_factual_claim(s) and not re.search(r"\[\d+\]", s)]
    if uncited_factual:
        return ValidationResult(
            ok=False,
            complaint=f"These sentences make factual claims without [n] citations: {uncited_factual[:3]}. Add citations or remove them."
        )

    return ValidationResult(ok=True)
```

`is_factual_claim()` is heuristic — it flags sentences containing a noun + a copula/attribution verb. The heuristic doesn't need to be precise because false positives just trigger one retry; false negatives are caught by reviewers when reading.

**Retry budget: one.** Two reasons:
- Two retries means we're papering over a bad prompt. Fix the prompt.
- Cost. Each retry doubles the Anthropic spend on a single artifact summary.

After a second failure: log the interaction, raise `SynthesisGroundingError`, return a degraded `ToolResponse` with `summary` populated from the structured fact list (no narrative) and `data.synthesis: null`.

## Anthropic call shape

Locked here for parity across `summarize_artifact` and `interpret_token`:

```python
response = client.messages.create(
    model="claude-sonnet-4-6",                  # see decisions.md for model rationale
    max_tokens=2048,                            # synthesis is short; reject anything longer
    system=[
        {
            "type": "text",
            "text": SYSTEM_PROMPT,              # versioned, file-backed in prompts/
            "cache_control": {"type": "ephemeral"},
        }
    ],
    messages=[
        {"role": "user", "content": render_facts_block(facts) + "\n\n" + intent}
    ],
    thinking={"type": "adaptive"},
    output_config={"effort": "medium"},
)
```

- **System cached** — facts vary per artifact, system prompt does not. Cache hit on every call after the first ~1.25× write.
- **`thinking.adaptive`** — lets Claude self-decide whether grounding needs reasoning. Cheaper than always-on extended thinking.
- **`effort: medium`** — synthesis is constrained generation, not open-ended reasoning. Higher effort overthinks and produces longer, harder-to-validate text.
- **No `temperature` / `top_p`** — would 400 on Opus 4.7 anyway, and synthesis is grounded so variance is unwelcome.

## Future: format-pluggable rendering

The `Citation` object stores **components**, so any of these styles is a pure projection:

```python
def render_citation(c: Citation, style: str = "inline") -> str:
    match style:
        case "inline":           # default: "[3]"
            return f"[{c.n}]"
        case "short":            # "(Parpola 1987:14)"
            return f"({c.publication_short}:{c.page_ref or ''})"
        case "chicago_author":   # "Parpola, S. 1987. Title. Helsinki."
            ...
        case "aaa_field":        # American Anthropological Association style
            ...
        case "csl_json":         # for Zotero/Pandoc round-tripping
            ...
        case "bibtex":           # for LaTeX users
            ...
```

**Not implemented in v1.** Tracked in [decisions.md](decisions.md) as roadmap. The contract is: client requests style, server returns rendered citations. No information loss between styles because the underlying object has all components.

## Litmus tests (the contract is honored iff)

1. `summarize_artifact("P227657")` returns synthesis with at least one `[n]` marker and `synthesis_citations` covers every marker.
2. Mocking Claude to return *"This tablet is Ur III"* (no marker) → validator complains, retry triggered.
3. Mocking Claude to return *"This tablet is Ur III [99]"* with no Fact 99 → validator complains, retry triggered.
4. Mocking Claude to fail twice → `SynthesisGroundingError`, response carries `data.synthesis: null` and `summary` from structured facts only.
5. `summarize_artifact("P_low_completeness")` (completeness ≤ 2 with ≥3 similar tablets) → `data.best_guess` populated, every hypothesis cites supporting facts, phrasing uses "resembles" not "is".
