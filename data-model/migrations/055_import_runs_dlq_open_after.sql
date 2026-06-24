-- Migration 055: import_runs.dlq_open_after — dead-letter open-count baseline.
--
-- Issue #175 (dead-letter P3: open-count alerting per run, no silent growth).
--
-- The ingestion framework routes every record it cannot integrate into
-- import_dead_letters (the triage queue). CLAUDE.md's non-negotiable is that
-- failures must never grow in the dark. To detect *growth* — not just an
-- absolute size — each run needs to know how many open dead letters this
-- connector had at the end of its PREVIOUS run, so the post-run check can say
-- "this run added N new open dead letters past the tolerance → ALERT".
--
-- This column stores the open dead-letter count for the run's connector,
-- captured at the end of the run (ingestion.dlq_alerts.check_and_alert writes
-- it). The next run reads the most recent non-NULL value for the same connector
-- as its baseline. Comparing run-to-run (rather than to a fixed ceiling) means
-- a connector with a known, triaged backlog doesn't false-alarm — only NEW
-- bleeding pages.
--
-- Nullable on purpose: runs from before this migration, and runs where the
-- alerting code failed defensively, simply carry NULL and are skipped when
-- choosing a baseline (the check then treats the baseline as 0).
--
-- GRANT: import_runs already grants the app (glintstone) its read/write set;
-- ADD COLUMN inherits the table's existing privileges, so no new GRANT is
-- required. The column is written by the ingestion runner, which connects as
-- the table owner.
--
-- Idempotent: ADD COLUMN IF NOT EXISTS makes a re-run a no-op.

BEGIN;

ALTER TABLE import_runs
    ADD COLUMN IF NOT EXISTS dlq_open_after INTEGER;

COMMENT ON COLUMN import_runs.dlq_open_after IS
    'Open dead-letter count (resolution_status=''open'') for this run''s '
    'connector, captured at end of run. The next run uses the most recent '
    'non-NULL value as its baseline to detect open-DLQ growth (issue #175). '
    'NULL for pre-#175 runs; skipped when picking a baseline.';

COMMIT;
