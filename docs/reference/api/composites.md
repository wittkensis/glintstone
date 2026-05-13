# Composites

Composite texts are scholarly groupings of multiple tablets that together constitute a single literary work. They are identified by Q-numbers (e.g., `Q000039`), the CDLI convention for composite identifiers. Individual tablets that contribute to a composite are called **exemplars**.

---

## List composites

```
GET /composites
```

Paginated list of composite texts with optional filtering.

**Query parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `language` | string | Filter by language |
| `period` | string | Filter by period |
| `genre` | string | Filter by genre |
| `search` | string | Search in designation |
| `limit` | integer | Maximum results, max 500 (default: `100`) |
| `offset` | integer | Results to skip (default: `0`) |

**Response**

```json
{
  "items": [
    {
      "q_number": "Q000039",
      "designation": "Gilgamesh, tablets i-xii",
      "language": "Akkadian",
      "period": "Neo-Assyrian (ca. 911-612 BC)",
      "genre": "Literary",
      "exemplar_count": 73
    }
  ],
  "total": 4821,
  "limit": 100,
  "offset": 0
}
```

---

## Composite detail

```
GET /composites/{q_number}
```

Full metadata for a single composite plus its list of exemplar tablets.

**Response**

```json
{
  "composite": {
    "q_number": "Q000039",
    "designation": "Gilgamesh, tablets i-xii",
    "language": "Akkadian",
    "period": "Neo-Assyrian (ca. 911-612 BC)",
    "genre": "Literary"
  },
  "exemplars": [
    { "p_number": "P338432", "designation": "Nineveh tablet", "museum_number": "K.3375" }
  ]
}
```

Returns 404 if the Q-number does not exist.

---

## Composite exemplars

```
GET /composites/{q_number}/exemplars
```

All exemplar tablets for a composite, without the composite metadata.

**Response**

```json
{
  "q_number": "Q000039",
  "count": 73,
  "exemplars": [
    { "p_number": "P338432", "designation": "Nineveh tablet", "museum_number": "K.3375" }
  ]
}
```
