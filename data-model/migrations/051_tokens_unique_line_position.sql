-- Migration 051: UNIQUE (line_id, position) on tokens
--
-- Issue #273 (Fix A) — the GATE for the new `oracc-atf` connector.
--
-- WHY:
--   The `oracc-atf` connector parses ORACC corpusjson CDL into text_lines and
--   tokens. To be safe to re-run (idempotent), its token inserts use
--   `ON CONFLICT (line_id, position) DO NOTHING`. Postgres requires a real
--   unique constraint/index for an ON CONFLICT target, and `tokens` had only a
--   primary key on `id`. Without this constraint a second run of the connector
--   would duplicate every token row.
--
--   This also mirrors the (line_id, position) uniqueness the existing
--   `oracc-lemmatizations` connector already assumes when it builds its
--   token_cache keyed on (line_id, position) — that assumption is now enforced
--   structurally rather than relied upon by convention.
--
-- SAFETY (verified against prod 2026-06-22 before writing this migration):
--   - 0 duplicate (line_id, position) groups across all 5,098,761 token rows,
--     so the constraint can be created without a backfill/dedup step.
--   - 0 tokens with NULL position. NULLs are treated as distinct by a UNIQUE
--     constraint, but there are none, so the constraint is fully enforcing for
--     every existing row. (The atf-parser and oracc-atf connectors always write
--     a concrete 0-indexed position, so no NULLs are introduced going forward.)
--
-- IDEMPOTENT: uses a guarded DO block so re-applying is a no-op (ADD CONSTRAINT
-- has no IF NOT EXISTS form in Postgres 17). The migration runner wraps this
-- file in a transaction; building the unique index briefly locks `tokens`,
-- which is acceptable (the prod table is ~5M rows and the deploy runs the
-- migration during a maintenance step, not under live write load).
--
-- GRANT: tokens is already granted to glintstone (migration 040). A unique
-- constraint adds no new grantable object, so no GRANT is needed here.

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'tokens_line_id_position_key'
          AND conrelid = 'public.tokens'::regclass
    ) THEN
        ALTER TABLE tokens
            ADD CONSTRAINT tokens_line_id_position_key UNIQUE (line_id, position);
    END IF;
END $$;

COMMENT ON CONSTRAINT tokens_line_id_position_key ON tokens IS
    'Issue #273: enables idempotent ON CONFLICT (line_id, position) DO NOTHING '
    'token inserts for the oracc-atf connector. One token per line position.';

COMMIT;
