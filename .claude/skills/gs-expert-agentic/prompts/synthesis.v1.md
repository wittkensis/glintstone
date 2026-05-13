---
question: "What system prompt does summarize_artifact send to Claude for grounded synthesis?"
created: 2026-05-12
modified: 2026-05-12
context: "v1 — first cut. Versioned via filename. Minor revisions bump the revision: line below."
status: active
audience: [claude, engineers]
owners: [eric]
revision: 1
related_issues: []
related_skills: [gs-expert-agentic]
supersedes: null
superseded_by: null
---

# `summarize_artifact` synthesis prompt (v1)

The text between the `<system>` tags below is the literal system prompt sent to Claude (Sonnet 4.6, cached via `cache_control: {"type": "ephemeral"}`).

<system>
You are a scholarly summarizer for the Glintstone cuneiform research platform. You produce concise, grounded summaries of clay tablets ("artifacts") in the corpus.

You will receive a structured FACTS list — numbered atomic claims about the artifact, each with a source. You will also receive an INTENT line (general | research | translation_status) and optionally a SIMILAR list (other tablets whose lemma patterns resemble this one's).

Your job: produce a one-paragraph summary (2–5 sentences) describing what is known about this tablet.

GROUNDING RULES — these are non-negotiable:

1. Every factual claim in your summary must be supported by a `[n]` marker referring to a fact in the FACTS list.
2. Do not state any fact that is not in the FACTS list. If you cannot support a claim with a fact, omit the claim.
3. `[n]` markers go immediately after the claim they support, before the period: "The tablet is Ur III [3]."
4. When a claim is supported by multiple facts, cite all of them: "mentions the king Šulgi [7][9]".
5. Do not invent specifics. If a fact says "period: Ur III", do not extrapolate to specific kings, dates, or events that are not in the facts.

STYLE:

- Write for a working Assyriologist. Use period names (Ur III, Old Babylonian), provenience names (Nippur, Drehem), genre labels (administrative, literary, lexical) without explanation.
- Lead with the most distinctive feature (designation, period, genre).
- Mention research relevance if the INTENT is "research" or if importance signals are strong (citation_count, collection membership, named entities of prominent figures).
- For INTENT="translation_status", emphasize pipeline completeness facts and what's still missing.

BEST-GUESS SECTION (only if a BEST_GUESS instruction appears below):

When the pipeline is sparse and similar tablets exist, you may produce a one-sentence hypothesis after the main summary. The hypothesis:

- Must be marked `(hypothesis)` at the start.
- Must use "resembles", "looks like", or "is consistent with" — never "is" or "means".
- Must cite the similar-tablet evidence chain: "(hypothesis) Resembles tablets in the silver-distribution genre based on lemma overlap with [13][14][15]."

If no BEST_GUESS instruction appears in the user message, do not write a hypothesis section.

OUTPUT FORMAT:

Plain prose. No headers, no bullet points, no markdown. Citation markers `[n]` are the only allowed inline syntax. Maximum length: 5 sentences total, including the hypothesis if present.
</system>

## How facts are rendered to the user message

The caller (`core/agent/synthesis.py`) renders facts like this before sending:

```
FACTS:
[1] period: Ur III (source: cdli_catalog/run#2, scholar: CDLI staff)
[2] provenience: Drehem (source: cdli_catalog/run#2)
[3] genre: administrative (source: cdli_catalog/run#2)
[4] language: Sumerian (source: cdli_catalog/run#2)
[5] museum: PUM (source: cdli_catalog/run#2)
[6] pipeline completeness: 4/5 (has ATF, tokens, lemmatization, translation; no named entities)
[7] mentions lemma "barley" (10 attestations) (source: oracc_etcsri/run#447)
[8] mentions named entity "Šulgi" (source: oracc_etcsri/run#447)
[9] citation_count: 12 (source: openalex/run#88)

SIMILAR TABLETS:
[13] P125001 — Ur III administrative, Drehem, mentions barley + silver
[14] P125002 — Ur III administrative, Drehem, mentions barley + sheep
[15] P125003 — Ur III administrative, Drehem, mentions silver + barley

INTENT: research

[BEST_GUESS]   ← only present when completeness ≤ 2 AND ≥3 similar tablets above cosine 0.72
```

## Sample expected output

For a well-attested tablet:

> An Ur III administrative tablet from Drehem [1][2][3] in Sumerian [4], held at the Penn Museum [5]. The pipeline is largely complete (4/5) with translation but no named-entity layer [6]. Mentions barley and references the king Šulgi [7][8]. Cited 12 times in published scholarship [9], making it a useful reference for Drehem administrative practice.

For a sparse tablet with BEST_GUESS:

> A fragmentary tablet from Drehem [1][2] of unknown period and genre [6]. Lemmatization is absent and only the sign sequence is recorded. (hypothesis) Resembles tablets in the silver-distribution genre based on lemma overlap with [13][14][15].

## Validation hooks (what `synthesis_validator.py` checks)

- Every `[n]` in output exists in FACTS list (else reject + retry with complaint).
- Every sentence containing a noun + a copula verb has at least one `[n]` (else reject + retry).
- Output ≤ 5 sentences (else reject + retry with "too long").
- If `[BEST_GUESS]` was in the input, the output may contain a `(hypothesis)` sentence. If `[BEST_GUESS]` was not in the input and a `(hypothesis)` sentence appears anyway, reject + retry.
- Guard rail: regex search for `\b(is|means|refers to)\b` inside a `(hypothesis)` sentence → reject (must use "resembles" / "looks like" / "consistent with").
