# Search & Agentic

These endpoints power the MCP tools and support AI-assisted research workflows. They return structured `ToolResponse` envelopes with sources for citation.

---

## Hybrid search

```
GET /search
```

Hybrid semantic + lexical search across tablets, lemmas, signs, scholars, publications, named entities, and composites. Uses Reciprocal Rank Fusion to merge lexical and semantic result lists.

**Query parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | **Required.** Free-text query |
| `types` | string[] | Restrict to entity types: `tablets`, `lemmas`, `signs`, `scholars`, `publications`, `entities`, `composites`. Omit for all. |
| `limit` | integer | Per-group result limit (default: 5, max: 100) |
| `cursor` | string | Opaque pagination cursor returned by previous response. 5-minute TTL. |
| `mode` | string | `hybrid` (default), `lexical`, or `semantic` |

**Response** — `ToolResponse[GroupedTablePayload]`

```json
{
  "data": {
    "groups": [
      {
        "group_type": "tablets",
        "items": [
          { "p_number": "P227657", "designation": "...", "pipeline_stage": "transcribed" }
        ]
      }
    ]
  },
  "summary": "Found 12 tablets matching 'grain distribution' in Ur III period...",
  "sources": [
    { "label": "CDLI", "url": "https://cdli.earth/P227657" }
  ],
  "interaction_id": "42"
}
```

The `interaction_id` is an integer (as string) that identifies this interaction in the `agent_interactions` table. Pass it to `submit_correction` if you need to correct a claim made based on these results.

---

## Artifact summary

```
GET /artifacts/{p_number}/summary
```

Grounded narrative summary of a single artifact. Lazy-cached: first call generates via Claude, subsequent calls return the cached result until any cited `annotation_run` is superseded by newer data.

For sparse tablets (pipeline completeness ≤ 2), if similar tablets exist in the corpus, the response includes a best-guess section phrased as hypotheses with its own evidence chain.

Every claim in the summary cites a source.

**Query parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `focus` | string | `general` (default), `research`, or `translation_status` |

**Response** — `ToolResponse[CardPayload]`

```json
{
  "data": {
    "title": "P227657 — KTT 188",
    "sections": [
      { "heading": "Overview", "body": "Administrative tablet from Ur III period..." },
      { "heading": "Text", "body": "The tablet lists grain rations for..." }
    ]
  },
  "summary": "Administrative Ur III tablet recording grain rations.",
  "sources": [...],
  "interaction_id": "43"
}
```

---

## Token interpretation

```
GET /artifacts/{p_number}/tokens/{token_id}/interpret
```

Walk the reading chain for a single token.

When the token is lemmatized: returns the complete chain — written form → normalized form → lemma → sense — with sources for each step.

When the token lacks lemmatization: returns 1–3 ranked hypotheses with confidence bands and evidence chains. Evidence draws from: candidate sign readings (from OGSL), neighbor context (surrounding tokens), genre and period priors. Hypotheses are always phrased as "resembles" or "consistent with" — never "is X" or "means X."

**Path parameters**

| Parameter | Description |
|-----------|-------------|
| `p_number` | CDLI P-number |
| `token_id` | `tokens.id` — discover via search results or the artifact ATF endpoint |

**Response** — `ToolResponse[ChainPayload]`

```json
{
  "data": {
    "form": "lu₂-gal",
    "chain": [
      { "step": "written_form", "value": "lu₂-gal", "source": "CDLI ATF" },
      { "step": "normalized", "value": "lugal", "source": "normalization bridge" },
      { "step": "lemma", "value": "lugal[king]N", "source": "ePSD2" },
      { "step": "sense", "value": "king, ruler", "source": "ePSD2" }
    ]
  },
  "summary": "lu₂-gal → lugal[king]N",
  "sources": [...],
  "interaction_id": "44"
}
```

---

## Submit correction

```
POST /agentic/corrections
```

Record a scholarly correction of an agent claim. The correction becomes a new `annotation_runs` row with `method='agent-hypothesis-correction'`. Any cached agent output that cited the corrected annotation is invalidated on the next request.

**Request body**

```json
{
  "interaction_id": 42,
  "claim": "The agent said this token means 'king'",
  "correction": "This reading is incorrect; the sign here should be read as...",
  "scholar_id": 1234,
  "evidence": "See Krecher 1969, p. 45"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `interaction_id` | yes | From `ToolResponse.interaction_id` of the response being corrected |
| `claim` | yes | The specific claim that is wrong |
| `correction` | yes | The correct interpretation |
| `scholar_id` | no | Links to `scholars` table for attribution |
| `evidence` | no | Scholarly citation supporting the correction |

**Response**

```json
{
  "interaction_id": 42,
  "feedback_id": 17,
  "new_annotation_run_id": 88,
  "message": "Correction recorded. The next request that re-loads any agent output citing the corrected annotation will regenerate."
}
```

Corrections are permanent. They do not delete existing data — they layer on top as a new annotation run.
