# Dictionary

The dictionary API exposes Glintstone's lexical layer: cuneiform signs (from OGSL), lemmas (from ePSD2 and ORACC glossaries), and gloss groups. All three levels are browseable and filterable.

---

## Browse

```
GET /dictionary/browse
```

Paginated browse of the lexical database at one of three levels.

**Query parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `level` | string | `lemmas` (default), `signs`, or `glosses` |
| `search` | string | Free-text search |
| `language` | string[] | Language filter (e.g., `sux`, `akk`, `akk-x-stdbab`) |
| `pos` | string[] | Part-of-speech filter — applies to `lemmas` and `glosses` levels |
| `source` | string[] | Source filter (e.g., `epsd2`, `ogsl`) — applies to `lemmas` and `signs` |
| `frequency` | string | Frequency tier filter — applies to `lemmas` level |
| `sort` | string | Sort order (default: `frequency`) |
| `page` | integer | Page number, 1-based (default: `1`) |
| `per_page` | integer | Results per page, max 200 (default: `50`) |

**Example — browse Sumerian lemmas**

```
GET /dictionary/browse?level=lemmas&language=sux&sort=frequency&per_page=25
```

---

## Filter options

```
GET /dictionary/filter-options
```

Returns available filter values at the given level given the currently active filters. Same parameters as browse (`level`, `language[]`, `pos[]`, `source[]`, `frequency`).

---

## Sign detail

```
GET /dictionary/signs/{sign_id}
```

Detail for a single cuneiform sign by its integer ID. Includes Unicode codepoint, all known readings/values, sign list references (OGSL), and GDL structural definition for compound signs.

---

## Lemma detail

```
GET /dictionary/lemmas/{lemma_id}
```

Detail for a single lemma by its integer ID. Includes citation form, guide word, part of speech, language, source, senses, and attestation count.

---

## Written-form lookup

```
GET /dictionary/lookup?form={form}
```

Look up candidate lemmas for a written orthographic form via the normalization bridge. Traverses: written form → normalized form → lemma → glosses. Returns candidates ranked by attestation frequency.

**Query parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `form` | string | **Required.** The written/orthographic form to look up |
| `language` | string | Optional language filter (e.g., `akk`, `sux`) |

**Example**

```
GET /dictionary/lookup?form=lugal&language=sux
```

---

## Normalized forms for a lemma

```
GET /dictionary/lemmas/{lemma_id}/norms
```

All normalized forms and their written spellings for a lemma.

**Response**

```json
{
  "lemma_id": 42,
  "norms": [
    { "normalized_form": "lugal", "written_spellings": ["lu₂-gal", "lugal"] }
  ]
}
```

---

## Gloss detail

```
GET /dictionary/glosses/{guide_word}
```

All lemmas sharing a guide word (gloss group). The `guide_word` path parameter is URL-encoded. Optionally filter by part of speech.

**Query parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pos` | string | Optional part-of-speech filter |

**Example**

```
GET /dictionary/glosses/king?pos=N
```
