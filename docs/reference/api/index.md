# API Reference

**Base URL:** `https://api.glintstone.org`

No authentication required. All read endpoints are publicly accessible. The collections endpoints support write operations.

## Error shape

```json
{ "detail": "Human-readable message" }
```

| Code | Meaning |
|------|---------|
| 404 | Resource not found |
| 422 | Validation error (invalid query parameter) |
| 500 | Internal server error |

## Pagination

List endpoints accept `page` (1-based, default 1) and `per_page` (default 24). The response includes `total`, `page`, and `per_page`.

```json
{
  "items": [...],
  "total": 353283,
  "page": 1,
  "per_page": 24
}
```

## Endpoint groups

| Group | Description |
|-------|-------------|
| [Artifacts](/docs/reference/api/artifacts/) | Search, detail, ATF, images, lemmas |
| [Search & Agentic](/docs/reference/api/search-agentic/) | Hybrid semantic search, AI summaries, token interpretation, corrections |
| [Dictionary](/docs/reference/api/dictionary/) | Signs, lemmas, glosses, written-form lookup |
| [Collections](/docs/reference/api/collections/) | Personal research sets (read/write) |
| [Composites](/docs/reference/api/composites/) | Multi-tablet composite texts (Q-numbers) |
| [Stats & Meta](/docs/reference/api/stats/) | Aggregate counts, health check, version, image serving |

The interactive Swagger UI is at [api.glintstone.org/docs](https://api.glintstone.org/docs).
