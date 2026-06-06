-- Migration 041: Extend annotation_runs method CHECK constraint for agentic values
--
-- Context: annotation_runs.method is governed by a named CHECK constraint
-- (annotation_runs_method_check), NOT a separate vocabulary table. The PRD-008
-- design assumed a table called annotation_runs_method existed; it does not.
--
-- Migration 025 seeded four agent method values inside a DO $$ IF EXISTS $$ guard
-- that checked for a table that never existed — so those INSERTs never ran. The
-- constraint still only contains the original 12 values from the baseline:
--   hand_copy, photograph, collation, autopsy, RTI, 3D_scan, ML_model,
--   import, api_fetch, web_scrape, manual, model
--
-- Production breakage: api/routes/agent.py line 231 already inserts
-- method='agent-hypothesis-correction', which the current constraint rejects.
--
-- This migration drops and recreates the constraint to include all agentic
-- method values — those seeded in 025 (but never applied) plus the three new
-- ones from PRD-008.

BEGIN;

ALTER TABLE annotation_runs
    DROP CONSTRAINT annotation_runs_method_check;

ALTER TABLE annotation_runs
    ADD CONSTRAINT annotation_runs_method_check CHECK (
        method = ANY (ARRAY[
            -- original baseline values
            'hand_copy',
            'photograph',
            'collation',
            'autopsy',
            'RTI',
            '3D_scan',
            'ML_model',
            'import',
            'api_fetch',
            'web_scrape',
            'manual',
            'model',
            -- agentic values (025 intended but never applied; now authoritative)
            'agent-hypothesis',
            'agent-summary',
            'agent-hypothesis-correction',
            'user-correction',
            -- PRD-008 new methods
            'agent-artifact-summary',
            'agent-line-suggestion',
            'agent-line-suggestion-accepted'
        ])
    );

COMMIT;
