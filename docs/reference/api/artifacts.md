# Artifacts

Artifacts are individual cuneiform objects — tablets, prisms, cones, and other carriers of writing. Each is identified by a P-number (e.g., `P227657`), the universal join key inherited from CDLI.

For the hybrid semantic search endpoint and AI-powered summary/token endpoints, see [Search & Agentic](/docs/reference/api/search-agentic/).

---

## Search artifacts

```
GET /artifacts
```

Full-text and faceted search across the corpus. Returns a paginated list of artifact summaries including thumbnail URLs.

**Query parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Free-text search against designation, museum number, and transliteration |
| `pipeline` | string | Filter by pipeline stage: `captured`, `recognized`, `transcribed`, `lemmatized`, `translated` |
| `period` | string[] | One or more periods (repeatable: `?period=Ur+III&period=Old+Babylonian`) |
| `provenience` | string[] | One or more proveniences |
| `genre` | string[] | One or more genres |
| `language` | string[] | One or more language codes |
| `has_ocr` | boolean | Only return artifacts with sign-detection annotations (default: `false`) |
| `page` | integer | Page number, 1-based (default: `1`) |
| `per_page` | integer | Results per page (default: `24`) |

**Example**

```
GET /artifacts?search=lugal&period=Ur+III&page=1&per_page=10
```

**Response**

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
  "per_page": 10
}
```

---

## Filter options

```
GET /artifacts/filter-options
```

Returns available values for each facet given the currently active filters. Used to build dynamic filter UIs that narrow as selections are made.

**Query parameters:** same as search (`period[]`, `provenience[]`, `genre[]`, `language[]`).

**Response**

```json
{
  "period": ["Ur III (ca. 2112-2004 BC)", "Old Babylonian (ca. 1900-1600 BC)", ...],
  "provenience": ["Nippur (mod. Nuffar)", "Ur (mod. Tell el-Muqayyar)", ...],
  "genre": ["Administrative", "Literary", "Legal", ...],
  "language": ["Sumerian", "Akkadian", ...]
}
```

---

## Artifact detail

```
GET /artifacts/{p_number}
```

Full metadata for a single artifact. Response includes all CDLI catalog fields: designation, museum number, excavation number, period, provenience, genre, language, material, object type, dimensions, primary publication, collection, and pipeline stage.

---

## ATF transliteration

```
GET /artifacts/{p_number}/atf
```

Parsed ATF transliteration with surface grouping.

**Response**

```json
{
  "atf": "obverse\n1. lugal-e ...",
  "parsed": {
    "surfaces": [
      {
        "name": "obverse",
        "lines": [
          { "line_no": "1.", "content": "lugal-e", "flags": [] }
        ]
      }
    ]
  },
  "legend": [...]
}
```

Returns 404 if no ATF data exists for this artifact.

---

## Translation

```
GET /artifacts/{p_number}/translation
```

Translation data grouped by language.

**Response**

```json
{
  "p_number": "P227657",
  "translations": {
    "en": [
      { "line_no": "1.", "text": "The king..." }
    ]
  }
}
```

---

## Images

```
GET /artifacts/{p_number}/images
```

Image manifest from the R2 cache. Each entry includes full-resolution URL, thumbnail URL, and display-ready credit line.

**Response**

```json
{
  "p_number": "P227657",
  "count": 2,
  "images": [
    {
      "id": 1,
      "image_type": "photo",
      "original_url": "https://assets.glintstone.org/...",
      "thumbnail_url": "https://assets.glintstone.org/...",
      "mime_type": "image/jpeg",
      "width": 1800,
      "height": 2400,
      "copyright_holder": "British Museum",
      "license": "CC BY-NC-SA 4.0",
      "credit_line": "© The Trustees of the British Museum",
      "display_order": 0
    }
  ]
}
```

---

## Ensure images

```
POST /artifacts/{p_number}/images/ensure
```

Idempotently fetches and caches CDLI images for an artifact into R2. Safe to call concurrently — a per-artifact lock prevents duplicate fetches. Returns immediately if rows already exist.

**Query parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `wait` | boolean | If `true` (default), blocks until fetch completes (~5–15s) and returns the image manifest. If `false`, schedules the fetch as a background task. |

---

## Normalized readings

```
GET /artifacts/{p_number}/normalized
```

Scholarly transliteration — the normalized reading of each sign as a structured list.

---

## Lemmatization

```
GET /artifacts/{p_number}/lemmas
```

Lemmatization data indexed by `(line_no, word_no)` for use in the ATF viewer. Each entry maps to a dictionary lemma.

**Response**

```json
{
  "p_number": "P227657",
  "total": 42,
  "lemmas": {
    "0": {
      "0": { "gw": "king", "cf": "lugal", "pos": "N", "epos": "N", "lang": "sux" }
    }
  }
}
```

---

## Sign annotations

```
GET /artifacts/{p_number}/sign-annotations
```

OCR bounding boxes for individual cuneiform signs, used to render overlay annotations on tablet images.

---

## Research context

```
GET /artifacts/{p_number}/research
```

Publications, scholars, and storage information for the Research tab — bibliographic context drawn from `publications`, `scholars`, and `artifact_editions`.

---

## Citation graph

```
GET /artifacts/citations/{doi}
```

Fetches citing papers from Semantic Scholar for a given DOI. The `doi` path parameter supports slashes (e.g., `10.1017/S0017383500001728`).
