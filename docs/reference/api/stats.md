# Stats & Meta

Aggregate metrics, health check, release information, and image serving.

---

## KPI metrics

```
GET /stats/kpi
```

Aggregate counts across the database — total artifacts, pipeline stage breakdown, row counts for the major tables. Used to populate the summary banner on the Data Integration page.

**Response** (representative; exact fields may extend as coverage grows)

```json
{
  "artifacts": 353283,
  "with_atf": 120000,
  "with_lemmatization": 7500,
  "with_translation": 43777,
  "text_lines": 1395668,
  "tokens": 3957240,
  "scholars": 20490,
  "publications": 16725
}
```

---

## Health check

```
GET /health
```

Confirms the API process and database connection are live. Returns 200 when healthy, 500 if the database is unreachable.

**Response**

```json
{ "status": "ok", "db": "ok" }
```

---

## Version

```
GET /version
```

Release tag, environment, applied schema version, and process start time.

**Response**

```json
{
  "release": "20260512-143022-a1b2c3d",
  "env": "production",
  "schema_version": 24,
  "started_at": "2026-05-12T14:30:22Z"
}
```

---

## Tablet image

```
GET /image/{p_number}
```

Serves a tablet photograph directly. Resolves the image from R2 storage and streams it as `image/jpeg`.

**Query parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `size` | integer | Optional thumbnail size in pixels. If provided, a square-cropped thumbnail is generated and cached. |

**Example**

```
GET /image/P227657         — full image
GET /image/P227657?size=200 — 200×200 thumbnail
```

Returns 404 if no image is available for the artifact.
