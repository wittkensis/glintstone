# Collections

Collections are personal research sets — named groups of artifacts that a user has curated. They are the only part of the API that supports write operations.

---

## List collections

```
GET /collections
```

Returns all collections.

**Response**

```json
{
  "items": [
    { "id": 1, "name": "Ur III Administrative", "description": "...", "tablet_count": 42 }
  ]
}
```

---

## Random collections

```
GET /collections/random
```

Returns a random sample of collections. Useful for discovery UI.

**Query parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Number of collections to return (default: `3`) |

---

## Collection detail

```
GET /collections/{collection_id}
```

Full metadata for a single collection.

---

## Collection tablets

```
GET /collections/{collection_id}/tablets
```

Paginated list of artifacts in a collection.

**Query parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number, 1-based (default: `1`) |
| `per_page` | integer | Results per page (default: `24`) |

---

## Create collection

```
POST /collections
```

**Request body**

```json
{ "name": "My Collection", "description": "Optional description" }
```

**Response:** the created collection object.

---

## Update collection

```
PUT /collections/{collection_id}
```

**Request body**

```json
{ "name": "Renamed", "description": "Updated description" }
```

Returns 404 if the collection does not exist.

---

## Delete collection

```
DELETE /collections/{collection_id}
```

**Response:** `{ "ok": true }`

---

## Add tablets to a collection

```
POST /collections/{collection_id}/tablets
```

**Request body**

```json
{ "p_numbers": ["P227657", "P123456"] }
```

**Response:** `{ "added": 2 }` — the count of rows inserted (duplicates are ignored).

---

## Remove a tablet from a collection

```
DELETE /collections/{collection_id}/tablets/{p_number}
```

**Response:** `{ "ok": true }`
