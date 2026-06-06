-- Migration 045: Add trust column to annotation_runs
--
-- Enables the trust signal in core/agent/fact_assembly.py (PRD-006 fix 2f).
-- The fact_assembly code already has a defensive try/except for UndefinedColumn;
-- once this migration runs the trust signal activates automatically.
--
-- trust: NULL = unknown (legacy rows), 0.0–1.0 = computed confidence.
-- Rows with trust < 0.7 get "(uncertain)" appended to their rendered facts.

BEGIN;

ALTER TABLE annotation_runs
    ADD COLUMN IF NOT EXISTS trust FLOAT
    CHECK (trust IS NULL OR (trust >= 0.0 AND trust <= 1.0));

GRANT SELECT, UPDATE ON annotation_runs TO glintstone;

COMMENT ON COLUMN annotation_runs.trust IS
    'Confidence score 0.0–1.0 for this annotation run. NULL = unscored. '
    'Values < 0.7 trigger (uncertain) labels in AI fact assembly.';

COMMIT;
