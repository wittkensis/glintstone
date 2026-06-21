---
question: "How do I write, apply, and verify a Postgres migration in Glintstone, and what's already been applied?"
created: 2026-05-11
modified: 2026-05-22
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
| 020 | `020_ingestion_staging.sql` | Staging tables for v2 ingestion framework |
| 021 | `021_source_snapshots.sql` | Tracks raw-source archive locations (B2/VPS) |
| 022 | `022_artifact_images.sql` | Tablet image metadata + R2 keys + copyright + fetch log |
| 023 | `023_artifact_images_null_dedup.sql` | Partial unique index closing the cdli_reader_id IS NULL gap in 022 |
| 024 | `024_connector_unique_constraints.sql` | Unique constraints + lexical_norm_forms cleanup for v2 ingestion connectors |
| 025 | `025_agentic_foundations.sql` | `pg_trgm` + pgvector extensions, trigram indexes, `entity_embeddings`, `agent_interactions`, `interaction_feedback`, `agent_outputs` |
| 026 | `026_search_entities.sql` | Matview `search_entities` (unified lexical surface) + view `pipeline_completeness` (0-5 score per artifact) |
| 027 | `027_users_and_sessions.sql` | `users`, `sessions`, `auth_methods` tables |
| 028 | `028_user_saved_items.sql` | `saved_items` table (bookmarks) |
| 029 | `029_user_avatar.sql` | `avatar_url` column on `users` |
| 030 | `030_filter_indexes.sql` | Additional indexes for filter queries |
| 031 | `031_pg_trgm.sql` | pg_trgm extension (trigram indexes) |
| 032 | `032_nfc_normalize_lexical.sql` | NFC normalization on lexical columns |
| 033 | `033_surface_type_expand.sql` | Expand `surface_type` enum values |
| 034 | `034_citation_fk_audit.sql` | FK audit and cleanup for citation pipeline |
| 035 | `035_compvis_orphan_audit.sql` | Orphan cleanup for compvis annotations |
| 036 | `036_artifact_image_fetch_log_page_outcomes.sql` | Widen `outcome` check constraint on `artifact_image_fetch_log` to include page-level outcomes |
| 037 | `037_user_roles.sql` | `role` column on `users` (admin/standard); seeds `eric.wittke@gmail.com` as admin |
| 050 | `050_artifact_contributors.sql` | #261 junction `artifact_contributors` (p_number × scholar × role) — real per-artifact attribution parsed from `artifact_credits` prose; backs the `/scholars/{id}/contributions` ledger |

**Always confirm `migrate.py status` matches this table.** If it doesn't, update one or the other.

## Rolling back

There is no automatic down-migration. If a migration is wrong:

1. Write a new migration that reverses it (e.g. `022_revert_021_*.sql`).
2. Apply forward.
3. Never edit a previously applied migration in place.
