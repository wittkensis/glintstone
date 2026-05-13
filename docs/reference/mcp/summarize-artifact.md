# summarize_artifact

Produce a grounded narrative summary of a single artifact (tablet).

## Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `p_number` | string | yes | — | CDLI P-number, e.g. `P227657` |
| `focus` | string | no | `general` | `general`, `research`, or `translation_status` |

**focus options:**
- `general` — overview of the tablet: period, genre, state of documentation, what the text contains if known
- `research` — emphasizes bibliographic context: editions, scholars, citation history
- `translation_status` — emphasizes what is and is not translated, what is lemmatized, what remains unknown

## Lazy caching

The first call to `summarize_artifact` for a given P-number is slower (~3–5 seconds) — the API calls Claude internally to generate the summary, then caches it in the `agent_outputs` table. Subsequent calls return the cached result immediately.

The cache is invalidated when any `annotation_run` cited by the summary is superseded by newer data. This means if a lemmatization is corrected or new ATF data arrives, the next summary request will regenerate.

## Sparse tablet behavior

When `pipeline_completeness ≤ 2` (the tablet has no ATF and no lemmatization), and similar tablets exist in the corpus (same period, provenience, genre), the response includes a best-guess section clearly framed as hypotheses:

- "Based on tablets with similar metadata from this period and provenience, this may be..."
- "The genre and period are consistent with administrative records of the type..."

Every claim in the best-guess section cites the tablets it draws from. Nothing is stated as fact when it is inference.

## Response

`ToolResponse[CardPayload]`:

```json
{
  "data": {
    "title": "P227657 — KTT 188",
    "sections": [
      {
        "heading": "Overview",
        "body": "Administrative clay tablet from the Ur III period (ca. 2112–2004 BC), provenience Ur..."
      },
      {
        "heading": "Text content",
        "body": "The tablet records grain rations (ninda, beer) in a school exercise format..."
      }
    ]
  },
  "summary": "Ur III administrative tablet; word list (school exercise), fully transliterated.",
  "sources": [
    { "label": "CDLI catalog", "annotation_run_id": 1 },
    { "label": "CDLI ATF", "annotation_run_id": 3 }
  ],
  "interaction_id": "43"
}
```
