# The API

The Glintstone REST API provides programmatic access to the full dataset — artifact metadata, ATF transliterations, lemmatizations, translations, lexical data, and more.

**Base URL:** `https://api.glintstone.org`

No authentication required. All endpoints return JSON.

## First request

Search for Ur III tablets mentioning "lugal" (king):

```
GET /artifacts?search=lugal&period=Ur+III
```

With curl:

```bash
curl "https://api.glintstone.org/artifacts?search=lugal&period=Ur+III"
```

## Response shape

```json
{
  "items": [
    {
      "p_number": "P227657",
      "designation": "CDLI Seals 001234",
      "period": "Ur III (ca. 2112-2004 BC)",
      "provenience": "Ur (mod. Tell el-Muqayyar)",
      "genre": "Administrative",
      "language": "Sumerian",
      "pipeline_stage": "transcribed",
      "thumbnail_url": "https://..."
    }
  ],
  "total": 1842,
  "page": 1,
  "per_page": 24
}
```

## Pagination

List endpoints accept `page` (1-based, default 1) and `per_page` (default 24). The response always includes `total`.

## Errors

Standard HTTP status codes. Error bodies:

```json
{ "detail": "Human-readable message" }
```

| Code | Meaning |
|------|---------|
| 404 | Resource not found |
| 422 | Validation error (invalid parameter) |
| 500 | Internal server error |

## Endpoint groups

- [Artifacts](/docs/reference/api/artifacts/) — search, detail, ATF, images, lemmas
- [Search & Agentic](/docs/reference/api/search-agentic/) — hybrid semantic search, AI summaries, token interpretation
- [Dictionary](/docs/reference/api/dictionary/) — signs, lemmas, written-form lookup
- [Collections](/docs/reference/api/collections/) — personal research sets
- [Composites](/docs/reference/api/composites/) — multi-tablet composite texts (Q-numbers)
- [Stats & Meta](/docs/reference/api/stats/) — counts, health, version

The interactive API reference (Swagger UI) is at [api.glintstone.org/docs](https://api.glintstone.org/docs).
