---
question: "How do I write, apply, and verify a Postgres migration in Glintstone, and what's already been applied?"
created: 2026-05-11
modified: 2026-05-11
context: "Created during the 2026-05-11 overhaul. The rolling 'applied migrations' table below is canonical — gs-curator-docs warns on push if source-data/migrations/ changed without this file updating."
status: active
audience: [claude, engineers]
owners: [eric]
related_issues: ["#3"]
related_skills: [gs-expert-data-model, gs-curator-docs]
supersedes: null
superseded_by: null
---

# Migrations workflow

## Where migrations live

- SQL files: `source-data/migrations/NNN_description.sql`
- Runner: `data-model/migrate.py`
- Tracking table: `public._migrations`

## Commands

```bash
# Show what's applied vs pending
python data-model/migrate.py status

# Apply all pending migrations
python data-model/migrate.py up

# Mark a migration as applied without running (recovery only)
python data-model/migrate.py mark-applied <version>
```

## Writing a new migration

1. Pick the next number: `ls source-data/migrations/ | tail -3` — increment by one.
2. Name: `NNN_short_description.sql` (lowercase, underscores).
3. Connect as `wittkensis` (the table owner), not `glintstone`.
4. Inside the file:
   ```sql
   BEGIN;

   CREATE TABLE my_new_table (...);
   CREATE INDEX my_new_table_idx ON my_new_table(...);

   -- IMPORTANT: GRANT to the app user
   GRANT SELECT, INSERT, UPDATE, DELETE ON my_new_table TO glintstone;
   GRANT USAGE, SELECT ON SEQUENCE my_new_table_id_seq TO glintstone;

   COMMIT;
   ```
5. Apply: `python data-model/migrate.py up`.
6. Verify: connect as `glintstone` user and confirm you can `SELECT`.
7. Update this file's table below.
8. If new tables, update `data-model/glintstone-schema.yaml`.
9. If new tables exercise interesting data, add a scenario to `.claude/skills/gs-curator-artifacts/catalog.yaml`.

## Connection strings

```bash
# Owner (for migrations)
/opt/homebrew/Cellar/postgresql@17/17.8/bin/psql -h 127.0.0.1 -U wittkensis -d glintstone

# App user (for read-only exploration)
PGPASSWORD=glintstone /opt/homebrew/Cellar/postgresql@17/17.8/bin/psql -h 127.0.0.1 -U glintstone -d glintstone

# Neon staging branch
psql "postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require"
```

The app reads `DATABASE_URL` from `.env`; switch environments by changing one line.

## Traps

### Rollback trap

In psycopg, `conn.rollback()` undoes **all** uncommitted changes in the transaction, not just the failed statement. So this pattern looks safe but is not:

```python
# WRONG — silently destroys earlier work in the transaction
try:
    cur.execute("INSERT INTO ... VALUES (...)")
except psycopg.errors.UniqueViolation:
    conn.rollback()
```

Use either `ON CONFLICT` or `NOT EXISTS`:

```python
cur.execute("""
    INSERT INTO t (k, v) VALUES (%s, %s)
    ON CONFLICT (k) DO NOTHING
""", (k, v))
```

### search_path

The pg_dump baseline sets `search_path = ''` at the cluster level. The migration runner explicitly qualifies `public._migrations`; don't strip that qualification — migrations will silently fail to register.

### Ownership

Tables are owned by `wittkensis`. The app connects as `glintstone`. After creating ANY new table or sequence, GRANT permissions to `glintstone`. Forgetting this surfaces as cryptic permission errors at runtime.

### Sequences

A `SERIAL` or `IDENTITY` column creates a sequence. Both need GRANTs:

```sql
GRANT USAGE, SELECT ON SEQUENCE my_table_id_seq TO glintstone;
```

## Applied migrations (rolling table — keep in sync with `_migrations`)

<!-- gs-curator-docs flags this table on push if source-data/migrations/ changed without this row count matching. -->

| Version | File | Purpose |
|---|---|---|
| 001–008 | various | Initial schema (artifacts, surfaces, lines, tokens, glossary) |
| 008 | `008_unified_lexical.sql` | Three-table unified lexical (signs, lemmas, senses) |
| 009 | `009_lexical_indexes.sql` | Indexes on `lexical_lemmas.citation_form` |
| 010 | `010_sign_lemma_assoc.sql` | Many-to-many bridge table |
| 011 | `011_lemmatization_language.sql` | Per-word `language` on `lemmatizations` (for bilingual tablets) |
| 012–014 | various | Translation matching, collection support |
| 015 | `015_lexical_tablet_occurrences.sql` | Pre-computed occurrence counts |
| 016 | `016_artifact_credits.sql` | ORACC per-text credit chain |
| 017 | `017_artifact_identifiers.sql` | Museum-number cross-references |
| 018–019 | various | Citation pipeline support |
| 020 | `020_*.sql` | Latest applied (verify with `migrate.py status`) |

**Always confirm `migrate.py status` matches this table.** If it doesn't, update one or the other.

## Rolling back

There is no automatic down-migration. If a migration is wrong:

1. Write a new migration that reverses it (e.g. `022_revert_021_*.sql`).
2. Apply forward.
3. Never edit a previously applied migration in place.
