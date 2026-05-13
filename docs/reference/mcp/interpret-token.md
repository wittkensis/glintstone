# interpret_token

Walk the reading chain for a single token on a tablet.

## Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `p_number` | string | yes | CDLI P-number |
| `token_id` | integer | yes | `tokens.id` — discover by searching first or browsing the artifact page |

To find `token_id`: call `semantic_search` with the P-number, or use the artifact ATF endpoint (`GET /artifacts/{p_number}/atf`) which returns token IDs in the parsed output.

## When lemmatized: the complete chain

If the token has an ORACC lemmatization, `interpret_token` returns the full reading chain with a source at each step:

```
written_form: "lu₂-gal"  [CDLI ATF, annotation_run 3]
  → normalized: "lugal"  [normalization bridge]
    → lemma: lugal[king]N  [ePSD2, annotation_run 7]
      → sense: "king, ruler; owner"  [ePSD2]
```

Each step cites its source. The chain is traceable to the original annotation run.

## When not lemmatized: ranked hypotheses

If the token has no lemmatization, `interpret_token` returns 1–3 ranked hypotheses. Each hypothesis is built from:

- **Candidate sign readings** — OGSL readings for the sign or sign sequence
- **Neighbor context** — what the surrounding tokens suggest about POS and semantic field
- **Genre and period priors** — what readings are most common in this genre and time period

**Phrasing constraints:** hypotheses are always phrased as:
- "resembles the pattern of..."
- "consistent with..."
- "may be a form of..."

They are never phrased as "is X" or "means X." The distinction matters: this is a hypothesis based on evidence, not a confirmed reading.

## Response

`ToolResponse[ChainPayload]`:

```json
{
  "data": {
    "form": "lu₂-gal",
    "p_number": "P227657",
    "token_id": 441,
    "chain": [
      { "step": "written_form", "value": "lu₂-gal", "source": "CDLI ATF" },
      { "step": "normalized", "value": "lugal", "source": "normalization bridge" },
      { "step": "lemma", "value": "lugal[king]N", "source": "ePSD2" },
      { "step": "sense", "value": "king, ruler; owner", "source": "ePSD2" }
    ],
    "hypotheses": null
  },
  "summary": "lu₂-gal → lugal[king]N (Sumerian noun, 'king')",
  "sources": [...],
  "interaction_id": "44"
}
```

When hypotheses are returned instead of a chain, `chain` is null and `hypotheses` is an array of ranked interpretations each with `confidence`, `evidence`, and `phrasing`.

## Correcting an interpretation

If the tool's reading is wrong, use `submit_correction` with the `interaction_id` from this response, the claim that was incorrect, and what it should say. See [submit_correction](/docs/reference/mcp/submit-correction/).
