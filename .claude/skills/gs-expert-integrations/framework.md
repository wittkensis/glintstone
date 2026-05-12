---
question: "What does a ingestion connector look like — anatomy, runner flow, RunContext API, and the v1→v2 port table?"
created: 2026-02-21
modified: 2026-05-11
context: "Deep reference companion to SKILL.md. Renamed from connector.md during the 2026-05-11 knowledge architecture overhaul and re-homed under gs-expert-integrations. The port table is the canonical authority on which v1 scripts have v2 equivalents."
status: active
audience: [claude, engineers]
owners: [eric]
related_issues: ["#60"]
related_skills: [gs-expert-data-model, gs-curator-docs]
supersedes: ".claude/skills/glintstone-connector/connector.md"
superseded_by: null
---

# ingestion — anatomy & port table

## Project context

- **Repo:** `/Volumes/Portable Storage/Glintstone`
- **Two-tier FastAPI:** API (port 8001) + web (port 8002) calling API via httpx
- **DB:** PostgreSQL 17, Neon production + local. Tables owned by `wittkensis`.
- **venv:** `source venv/bin/activate` — always activate before running Python
- **Tests:** `python -m pytest tests/ -q` (hits Neon, ~20s)
- **Servers:** `ops/local/start.sh`, uvicorn `--reload`
- **Migrations:** `python data-model/migrate.py status|up|mark-applied <ver>`

## Connector anatomy

```
ingestion/
  base.py          — SourceConnector, ModelConnector, RunContext, LoadStats
  runner.py        — run_connector() — wraps ETL + import_runs bookkeeping
  loader.py        — upsert_batch() — INSERT ... ON CONFLICT
  registry.py      — discover_connectors() — auto-discovers ingestion.connectors.*
  dead_letters.py  — DeadLetterSink, DeadLetterCategory
  cli.py           — python -m ingestion.cli list|run|status|dead-letters
  connectors/
    lookup_tables.py          — seeds 7 canon/normalization tables (runs first)
    cdli_catalog.py           — CDLI artifact catalog → staging_cdli_catalog
    translation_line_matcher.py — matches translations to text_lines
```

## Runner flow

```
discover() → checksum == last? → no_op
                               → extract() → transform() → load() → verify()
```

`transform()` is called record-by-record via `_flatten_transform()`. Default is identity `yield record`.

## Key classes

```python
class MyConnector(SourceConnector):
    id = "my-connector"          # stable slug; matches other connectors' runs_after
    display_name = "My Connector"
    kind = "catalog"             # catalog | corpus | lexicon | annotation | lookup | derived
    runs_after = ["lookup-tables"]
    license = "CC-BY-4.0"
    upstream_url = "https://..."

    def discover(self, ctx: RunContext) -> SourceManifest:
        # Return checksum to enable skip-if-unchanged. Default = always run.
        checksum = _file_checksum(path)
        return SourceManifest(checksum=checksum, raw_path=str(path))

    def extract(self, ctx: RunContext) -> Iterator[dict]:
        # Yield one raw dict per source record
        with open(path) as f:
            for row in csv.DictReader(f):
                yield row

    def transform(self, ctx: RunContext, record: dict) -> Iterator[dict]:
        # Validate + reshape. Dead-letter bad rows. Yield 0-N output rows.
        if not record.get("id"):
            ctx.dead_letter(category="validation_failed", payload=record, reason="missing id")
            return
        yield {"col_a": record["a"], "col_b": record["b"]}

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        return upsert_batch(ctx.db, table="my_table", rows=rows,
                            unique_key=["id"], policy=ConflictPolicy.UPDATE)

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute("SELECT COUNT(*) AS n FROM my_table").fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        if n < 1000:
            raise AssertionError(f"my_table has {n} rows; expected ≥ 1000")
```

## Multi-table connectors (lookup_tables pattern)

When one connector seeds multiple tables, tag each yielded row with `_target` and route in `load()`:

```python
def extract(self, ctx):
    for entry in STATIC_LIST:
        yield {"_target": "table_a", "col": entry}
    # scan CSV for dynamic values
    for raw in discovered_values:
        yield {"_target": "table_b", "raw": raw, "canonical": normalize(raw)}

def load(self, ctx, rows):
    by_target: dict[str, list[dict]] = {}
    for row in rows:
        target = row.pop("_target")
        by_target.setdefault(target, []).append(row)
    total = LoadStats()
    for table, batch in by_target.items():
        stats = upsert_batch(ctx.db, table=table, rows=batch,
                             unique_key=_TABLE_KEYS[table], policy=ConflictPolicy.UPDATE)
        total = total.merge(stats)
    return total
```

## upsert_batch

```python
upsert_batch(
    db,
    table="my_table",          # alphanumeric + underscore only
    rows=rows,                 # Iterable[dict] — all keys must be consistent
    unique_key=["id"],         # conflict target
    policy=ConflictPolicy.SKIP | UPDATE | REPLACE,
    batch_size=1000,           # default
)
# Returns LoadStats(inserted, updated, skipped, dead_lettered)
```

## RunContext methods

```python
ctx.info("event.key", col=val)     # logs to import_run_events + stdout
ctx.warn("event.key", ...)
ctx.error("event.key", ...)
ctx.dead_letter(
    category="validation_failed",  # from DeadLetterCategory enum
    subcategory="missing_id",
    source_key="P123456",
    payload=record,
    reason="no id field",
)
ctx.stats                           # LoadStats accumulator
ctx.db                              # psycopg connection
ctx.run_id                          # for correlation
```

## Running connectors

```bash
python -m ingestion.cli list
python -m ingestion.cli run lookup-tables
python -m ingestion.cli run cdli-catalog
python -m ingestion.cli status
python -m ingestion.cli dead-letters cdli-catalog
```

## Registry scoping

`discover_connectors()` only registers classes whose module starts with `ingestion.connectors`. Test fixtures defined in test files won't pollute production registry.

## `__init_subclass__` warning

Do NOT put connector validation in `__init_subclass__`. At class-creation time, ABCMeta hasn't populated `__abstractmethods__` yet — you can't distinguish abstract bases from concrete subclasses. Validation runs at registry-load time instead.

## Schema interactions

- Tables owned by `wittkensis`, not `glintstone`. Run migrations as `wittkensis`.
- GRANT permissions to glintstone user for every new table + sequence.
- Migrations: `source-data/migrations/NNN_*.sql` — latest applied: 020 (verify via `python data-model/migrate.py status`)
- `search_path` trap: the pg_dump baseline sets `search_path = ''`. The migration runner qualifies `public._migrations` explicitly — don't remove that qualification.

For psycopg gotchas, Jinja2 traps, and macOS SSL workarounds, see `gs-expert-data-model/query-patterns.md`.

## v1 → v2 port status (canonical table)

<!-- This table is the source of truth. gs-curator-docs flags it if ingestion/connectors/ changes without this table updating. -->

| v1 script | connector |
|---|---|
| `01_seed_lookup_tables.py` | `lookup_tables.py` |
| `02_seed_annotation_runs.py` | `annotation_runs.py` |
| `03_import_scholars.py` | `scholars.py` |
| `04_import_signs.py` | `ogsl_signs.py` |
| `05_import_artifacts.py` | `cdli_catalog.py` |
| `05b_enrich_artifacts_oracc.py` | `oracc_enrichment.py` |
| `05c_populate_genre_language_junctions.py` | `genre_language_junctions.py` |
| `06_seed_artifact_identifiers.py` | `artifact_identifiers.py` |
| `07_parse_atf.py` | `atf_parser.py` |
| `10_import_token_readings.py` | `token_readings.py` |
| `11_import_lemmatizations.py` | `oracc_lemmatizations.py` |
| `13_import_glossaries.py` | `oracc_glossaries.py` |
| `15_import_epsd2_unified.py` | `epsd2.py` |
| `16_import_oracc_glossaries.py` | `oracc_lexical_glossaries.py` |
| `18_import_norms.py` | `oracc_norms.py` |
| `19_match_translation_lines.py` | `translation_line_matcher.py` |
| `21_import_oracc_credits.py` | `oracc_credits.py` |
| `22_import_ebl_sign_concordance.py` | `ebl_sign_concordance.py` |
| `23_import_unicode_signs.py` | `unicode_signs.py` |
| (no v1; ML) | `baby_lemmatizer.py` |

Not ported: `00` (downloader), `17` (test script), `20` (needs archived SQLite), `15b/15c/15d/15e` (one-time cleanup).

Reference: `source-data/import-tools/README.md`
