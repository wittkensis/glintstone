---
question: "How do I query the database in Glintstone — repository pattern, cross-filter counts, psycopg row handling, Jinja2 traps?"
created: 2026-05-11
modified: 2026-05-11
context: "Pulled from skills-disabled/assyriology/SKILL.md (Jinja2 traps), the existing glintstone-connector skill (psycopg patterns), and PLAN/Engineer Onboarding Guide.md (repository pattern). Consolidated during the 2026-05-11 overhaul so UI/API work has this in one place."
status: active
audience: [claude, engineers]
owners: [eric]
related_issues: []
related_skills: [gs-expert-data-model, gs-expert-ui]
supersedes: null
superseded_by: null
---

# Query patterns

## Repository pattern

All SQL lives in `api/repositories/*_repo.py`. Repositories subclass `BaseRepository` from `core/repository.py`:

```python
from core.repository import BaseRepository

class ArtifactRepository(BaseRepository):
    def find_by_p_number(self, p_number: str) -> dict | None:
        return self.fetch_one(
            "SELECT * FROM artifacts WHERE p_number = %s",
            (p_number,),
        )
```

Routes get the repo via dependency injection:

```python
from fastapi import APIRouter, Depends
from core.database import get_db

router = APIRouter()

@router.get("/{p_number}")
def get_artifact(p_number: str, conn=Depends(get_db)):
    repo = ArtifactRepository(conn)
    return repo.find_by_p_number(p_number)
```

`BaseRepository` provides:

- `fetch_all(sql, params) -> list[dict]`
- `fetch_one(sql, params) -> dict | None`
- `build_in_clause(values) -> (sql, params)` — for `IN (...)` with parameterization

## Two-tier rule

The web layer (`app/`) never touches the DB. It calls the API via `httpx`:

```python
async def tablet_detail(request, p_number):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_URL}/artifacts/{p_number}")
    return templates.TemplateResponse("tablets/detail.html", {"artifact": resp.json()})
```

## Cross-filter counts

The filter sidebar shows how many results each option would produce, dynamically excluding the current dimension. The pattern lives in `api/repositories/artifact_repo.py`:

```python
def _cross_filter_where(self, active: dict, exclude: str) -> tuple[str, list]:
    """Build WHERE for all active filters EXCEPT the excluded dimension.
    So 'Period' counts reflect your Genre/Language/Provenience selections."""
    ...
```

So `period` counts use active `genre + language + provenience` filters; `genre` counts use active `period + language + provenience`; etc.

## psycopg gotchas

### Row results — dict OR index

`psycopg3` returns Row objects that support both dict and index access. The codebase uses this defensive pattern:

```python
row = ctx.db.execute("SELECT COUNT(*) AS n FROM artifacts").fetchone()
n = row["n"] if isinstance(row, dict) else row[0]
```

Use it consistently. Don't `row.n`.

### Rollback trap (also covered in migrations.md)

`conn.rollback()` undoes ALL uncommitted changes in the transaction. Use `ON CONFLICT` or `NOT EXISTS` instead of try/except `UniqueViolation`.

### Connection pool

`core/database.get_db()` yields connections from a pool. Don't hold a connection across an `await`; release it back to the pool.

### Server cursors for large reads

For >100k row reads, declare a server cursor or stream batches. The connection-pool default fetches everything into memory.

## Jinja2 traps

### Dict-method collision

If a dict key is named `items`, `values`, `keys`, `get`, or `update`, dot notation calls the Python dict method, not the key:

```jinja2
{{ section.items }}   {# This calls dict.items() — not the 'items' key #}
{{ section['items'] }}  {# Use bracket access, or rename the key (preferred) #}
```

Rename to `children`, `entries`, `options`, etc.

### No `in` test

`selectattr('val', 'in', some_list)` doesn't work — `'in'` is not a valid Jinja2 test. Use:

```jinja2
{% set ns = namespace(found=false) %}
{% for x in some_list %}
  {% if x == val %}{% set ns.found = true %}{% endif %}
{% endfor %}
{% if ns.found %}...{% endif %}
```

Or filter on the Python side and pass a boolean.

## macOS SSL workaround

Python `urllib`/`requests` can fail on macOS for some HTTPS endpoints. For import-time fetches, shell out to `curl`:

```python
import subprocess
out = subprocess.run(
    ["curl", "-fSsL", url],
    check=True, capture_output=True,
).stdout
```

## Performance notes

- `get_filter_options()` runs 4 `DISTINCT` queries against 353k rows on every page load. Issue #2 (caching) tracks the fix.
- `tokens` is 4M rows; always filter or LIMIT before scanning.
- The cross-filter pattern fires N separate `COUNT(*)` queries. Acceptable for now; cache when it shows up in profiling.

## Lexical lookups

The lexical API (`core/lexical.py`) wraps the 3-dimensional lexical model in convenient functions. See [lexical-api.md](lexical-api.md).
