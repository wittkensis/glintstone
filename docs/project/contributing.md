# Contributing

Glintstone is a small project with high standards for data integrity. Contributions — code, domain expertise, corrections — are welcome.

## Non-negotiables

- **Source attribution is structural.** Every annotation carries `annotation_run_id`. Never silently overwrite a previous annotation — always create a new run.
- **Two-tier rule.** The web app never touches the database directly. It calls the API over HTTP via httpx. New routes belong either in `api/` (JSON responses) or `app/` (HTML responses) — not both.
- **Migrations run as `wittkensis`.** Tables are owned by `wittkensis`; the app connects as `glintstone`. After creating any new table or sequence, GRANT permissions to `glintstone`.
- **Never push to main with red CI.** Never use `--no-verify`. Never modify the production database branch directly.
- **Competing interpretations are a feature.** Two scholars disagreeing on a lemma both get stored. Do not deduplicate based on agreement.

## Development setup

The project uses a local nginx proxy to match production routing. Start the full stack:

```bash
./ops/local/start.sh
```

This starts the API (port 8001) and web app (port 8002). Browse at `http://app.glintstone.test`. The API Swagger UI is at `http://api.glintstone.test/docs`.

Both servers run with `--reload` — Python file changes take effect immediately.

## Adding a migration

Migrations live in `data-model/migrations/NNN_*.sql`. Use `data-model/migrate.py` to apply:

```bash
python data-model/migrate.py
```

Always use `ON CONFLICT` or `NOT EXISTS` rather than try/except `UniqueViolation`. The psycopg rollback trap: `conn.rollback()` undoes ALL uncommitted work in the transaction, not just the failed statement.

After creating new tables or sequences, run:

```sql
GRANT ALL ON new_table TO glintstone;
GRANT USAGE, SELECT ON SEQUENCE new_table_id_seq TO glintstone;
```

## Adding a data source connector

Connectors live in `ingestion/connectors/`. Each implements the `SourceConnector` interface from `ingestion/base.py`:

```python
class MyConnector(SourceConnector):
    id = "my-connector"
    kind = "catalog"
    runs_after = ["lookup-tables"]
    license = "CC-BY-4.0"

    def discover(self, ctx) -> SourceManifest: ...
    def extract(self, ctx) -> Iterator[dict]: ...
    def transform(self, ctx, record) -> Iterator[dict]: ...
    def load(self, ctx, rows) -> LoadStats: ...
    def verify(self, ctx) -> None: ...
```

Run connectors via the CLI:

```bash
python -m ingestion.cli run <connector-name>
python -m ingestion.cli status
```

See `docs/engineer-onboarding.md` for the full Day 1–5 ramp-up, including the code reading order and common gotchas.

## Opening a pull request

- Keep PRs focused. One concern per PR.
- CI must be green before requesting review.
- Add tests for any new repository or API behavior.
- Document schema changes in `data-model/`.

## Domain expert contributions

You do not need to write code to contribute. If you are an Assyriologist and notice an error, a missing attribution, a wrong reading, or a gap in coverage: email [eric.wittke@gmail.com](mailto:eric.wittke@gmail.com) or use the `submit_correction` MCP tool if you are working through Claude.

We want to hear from domain experts. The data quality depends on it.
