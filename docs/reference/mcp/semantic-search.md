# semantic_search

Search the Glintstone corpus across tablets, lemmas, signs, scholars, publications, named entities, and composites.

## Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `q` | string | yes | — | Free-text query: a phrase, lemma form, P-number, scholar name, etc. |
| `types` | list[string] | no | all | Restrict to these entity types: `tablets`, `lemmas`, `signs`, `scholars`, `publications`, `entities`, `composites` |
| `limit` | integer | no | 5 | Per-group result limit (max 100) |
| `mode` | string | no | `hybrid` | Retrieval mode: `hybrid`, `lexical`, or `semantic` |

## Retrieval mode

**hybrid** — Reciprocal Rank Fusion over both lexical and semantic result lists. RRF works by scoring each document by the sum of `1/(k + rank)` across both lists, where `k=60`. This consistently outperforms either retrieval method alone, especially for domain terms that appear in both the controlled vocabulary (sign names, lemma forms) and natural language queries.

**lexical** — Full-text search over the indexed forms. Exact and near-exact matches. Use when you know the specific ATF form or P-number.

**semantic** — Vector similarity search over embedded representations. Use when you want conceptually related results rather than exact lexical matches.

## Response envelope

`semantic_search` returns a `ToolResponse[GroupedTablePayload]`:

```json
{
  "data": {
    "groups": [
      {
        "group_type": "tablets",
        "items": [{ "p_number": "P227657", "designation": "...", ... }],
        "view_all_url": "/artifacts?search=grain+distribution"
      }
    ]
  },
  "summary": "Found matching tablets in the Ur III administrative corpus...",
  "sources": [
    { "label": "CDLI", "annotation_run_id": 1 }
  ],
  "interaction_id": "42"
}
```

The `cursor` field in the response enables pagination — pass it as `cursor` in the next request to retrieve the next page. Cursors have a 5-minute TTL.

## Example invocations

```
semantic_search(q="grain distribution Ur III")
semantic_search(q="lugal", types=["lemmas", "tablets"])
semantic_search(q="P227657")
semantic_search(q="Piotr Steinkeller", types=["scholars"])
semantic_search(q="Epic of Gilgamesh", types=["composites"], limit=3)
```

## Attribution

Every result item carries source metadata. The `sources` array in the response lists the annotation runs that produced the data. Pass the `interaction_id` to `submit_correction` if any claim based on these results needs correction.
