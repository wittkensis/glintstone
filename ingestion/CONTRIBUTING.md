---
question: "How do I add a new data source to Glintstone's ingestion framework?"
created: 2026-05-18
modified: 2026-05-18
context: "The connector contract for the ingestion framework — SourceConnector lifecycle, RunContext API, LoadStats semantics, and dead-letter patterns. The canonical narrative also lives on the GitHub Wiki (Engineer Onboarding)."
status: active
audience: [engineers, claude]
owners: [eric]
related_issues: ["#63"]
related_skills: [gs-expert-integrations]
supersedes: null
superseded_by: null
---

# Adding a connector

Every connector is a subclass of `SourceConnector` (`ingestion/base.py`) registered in `ingestion/registry.py`. The framework guarantees:

- A `run_id` row in `import_runs` for every invocation.
- An `annotation_run_id` so downstream tables carry attribution (see CLAUDE.md — attribution is structural).
- Dead-letter routing through `import_dead_letters` whenever you can't load a record.
- Structured events in `import_run_events` keyed on the same `run_id`.

## The five lifecycle methods

```python
class MySourceConnector(SourceConnector):
    id = "my-source"
    display_name = "My Source"
    kind = "lexicon"          # catalog | corpus | lexicon | annotation | lookup | derived
    runs_after = ["lookup-tables"]
    license = "CC-BY-4.0"
    upstream_url = "https://example.org/api/data"
    citation = "Doe, Jane. 'My Source.' 2024."

    def discover(self, ctx: RunContext) -> SourceManifest: ...
    def extract(self, ctx: RunContext) -> Iterator[dict]: ...
    def transform(self, ctx: RunContext, record: dict) -> Iterator[dict]: ...
    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats: ...
    def verify(self, ctx: RunContext) -> None: ...
```

| Method | Purpose | Failure mode |
|---|---|---|
| `discover` | Establishes source manifest (URL, checksum, record count estimate). Cached per source-update. | Raises → run fails, nothing written. |
| `extract` | Streams raw records from upstream. Each yielded dict is opaque to the framework. | Raises → run fails. |
| `transform` | Maps each raw record to one or more rows shaped for `load`. Validation belongs here. | Per-record exception → `ctx.dead_letter(...)`; run continues. |
| `load` | Writes the transformed rows. Owns the DB transaction. Returns `LoadStats`. | Raises → run fails. Per-row conflict → `ON CONFLICT DO NOTHING` + `stats.skipped += 1`. |
| `verify` | Post-write sanity check (row count, FK integrity). | Raises → run marked failed *after* commit; data still landed. |

## `LoadStats` semantics

`inserted` — new rows written. `updated` — rows whose values changed under an `ON CONFLICT DO UPDATE`. `skipped` — conflicts that hit `DO NOTHING`, *or* expected-but-uninteresting cases (e.g. a token with no matching lemma when 90% don't match). `dead_lettered` — rows that couldn't load and got persisted to `import_dead_letters` for triage.

Never count a record in two buckets. The dashboard math depends on `inserted + updated + skipped + dead_lettered = total_transformed`.

## Dead letters

Use `ctx.dead_letter()` for one-off failures:

```python
try:
    norm_id = lookup_norm(record["norm"])
except KeyError:
    ctx.dead_letter(
        category="unresolved_norm",
        payload=record,
        reason=f"norm '{record['norm']}' not found in lexical_norms",
        source_key=record.get("id"),
    )
    return
```

Use `ctx.dead_letter_many()` for bulk failures (each call to the single-row variant commits, which is wasteful at scale).

The earlier oracc-lemmatizations connector counted 900k "no-lemma-match" cases as `dead_lettered` without writing them to `import_dead_letters` (issue #63). Don't do that — either persist them via `dead_letter()`, or reclassify as `skipped` if the no-match outcome is expected.

## Structured events

`ctx.info()`, `ctx.warn()`, `ctx.error()` write to `import_run_events` *and* to stdout/stderr. The runner already emits `run.start`, `run.completed`, and `run.failed` — connectors don't need to emit those. Emit your own events for milestones a developer might want to grep later:

```python
ctx.info("oracc.parse.start", total_glossaries=len(manifest))
# ...batch loop...
ctx.info("oracc.parse.batch", count=len(batch), running_total=total)
```

The `context=` kwargs land in `import_run_events.context::jsonb`. Keep them flat (no nested dicts), and avoid PII.

## The `runs_after` graph

The CLI resolves the connector graph topologically — declare every connector you depend on, even transitively. If `my-source` reads `lexical_lemmas.id`, it `runs_after = ["epsd2"]` and `["oracc-glossaries"]`.

## Postgres gotchas (from CLAUDE.md)

- `conn.rollback()` undoes every uncommitted change in the transaction — avoid `try/except UniqueViolation`. Use `ON CONFLICT (col) DO NOTHING` instead.
- Tables are owned by `wittkensis`; the runtime connects as `glintstone`. New tables and sequences need an explicit `GRANT SELECT, INSERT, UPDATE, DELETE` to `glintstone` in the migration that creates them.
- macOS Python `requests`/`urllib` can fail on some HTTPS endpoints. Shell out to `curl` via `subprocess.run(...)` when ingesting from an upstream that misbehaves.

## CLI reference

```
python -m ingestion.cli list                # all registered connectors
python -m ingestion.cli run <id>            # full run
python -m ingestion.cli run <id> --mode incremental
python -m ingestion.cli status <run_id>     # latest run summary
python -m ingestion.cli dead-letters <id>   # triage queue
```

## Scheduled runs

`.github/workflows/cron-ingest.yml` runs ORACC connectors weekly (Sunday 04:00 UTC) and CDLI monthly (5th, 05:00 UTC). Manual dispatch is supported — `gh workflow run cron-ingest.yml -f connector=oracc-norms -f mode=incremental`.

## Where to look next

- `ingestion/base.py` — the contract itself, with full docstrings.
- `ingestion/connectors/cdli_catalog.py` — well-commented reference connector.
- `.claude/skills/gs-expert-integrations/` — patterns and v1 → v2 porting notes.
- GitHub Wiki → `Engineer-Onboarding` page for the day-1 ramp.
