-- Migration 062: scholar_corrections — Level 2 Scholar Corrections (#532).
--
-- A verified scholar (one who holds an APPROVED scholar_claims row) can file a
-- correction against a model-generated artifact summary or a single-token
-- interpretation. This is the next rung above the bio overlay (#17): scholars
-- not only claim their identity, they now annotate the corpus's machine output
-- with expert corrections that admins review.
--
-- DECISIONS BAKED IN (research plan, Eric-approved):
--   1. A correction targets either a `summary` (whole-artifact synthesis, keyed
--      by p_number) or an `interpretation` (single token, keyed by token id) —
--      target_type + target_id is the polymorphic pointer. No FK on target_id
--      because the two target spaces (artifacts.p_number text, tokens.id) have
--      different key types; the API validates existence at write time.
--   2. correction_text is capped at 500 chars (a focused correction, not an
--      essay) — enforced in the DB (CHECK) AND the API so neither tier can be
--      bypassed.
--   3. reason is a closed enum (wrong_lemma / wrong_translation / missing_context
--      / other) so the queue can be triaged by failure mode.
--   4. status flows pending → reviewed/accepted/rejected; admin stamps
--      reviewed_by + a review_note. Default pending.
--
-- ATTRIBUTION IS STRUCTURAL (CLAUDE.md non-negotiable): every correction carries
-- annotation_run_id so a correction is provenance-linked to the run it critiques
-- — never an anonymous edit. annotation_runs.id is integer (baseline schema), so
-- the FK column is integer to match.
--
-- GRANT: the table is owned by wittkensis (migrations run as wittkensis); the app
-- connects as glintstone, so GRANT the CRUD set after creating the table.
--
-- Idempotent: CREATE TABLE IF NOT EXISTS + CREATE ... IF NOT EXISTS on every
-- index, so re-running the migration is a no-op.

BEGIN;

CREATE TABLE IF NOT EXISTS scholar_corrections (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    scholar_id        integer NOT NULL REFERENCES scholars(id) ON DELETE CASCADE,
    target_type       text    NOT NULL
                        CHECK (target_type IN ('summary', 'interpretation')),
    target_id         text    NOT NULL,            -- p_number (summary) | token id (interpretation)
    correction_text   text    NOT NULL
                        CHECK (char_length(correction_text) <= 500),
    reason            text    NOT NULL
                        CHECK (reason IN ('wrong_lemma', 'wrong_translation',
                                          'missing_context', 'other')),
    citation          text,                         -- optional supporting reference
    status            text    NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'reviewed', 'accepted', 'rejected')),
    annotation_run_id integer REFERENCES annotation_runs(id) ON DELETE SET NULL,
    review_note       text,                         -- admin's note (shown on the queue audit trail)
    reviewed_by       uuid REFERENCES users(id),    -- admin who acted; NULL until reviewed
    created_at        timestamptz NOT NULL DEFAULT now(),
    reviewed_at       timestamptz,                  -- stamped on accept/reject
    updated_at        timestamptz NOT NULL DEFAULT now()
);

-- The queue feed is "oldest pending first"; a partial index keeps that scan
-- cheap as the accepted/rejected history grows without bound.
CREATE INDEX IF NOT EXISTS idx_scholar_corrections_pending
    ON scholar_corrections (created_at) WHERE status = 'pending';

-- A scholar's own corrections (for a future "my corrections" surface).
CREATE INDEX IF NOT EXISTS idx_scholar_corrections_scholar
    ON scholar_corrections (scholar_id);

-- All corrections against one target (so a summary/token can show its dissent).
CREATE INDEX IF NOT EXISTS idx_scholar_corrections_target
    ON scholar_corrections (target_type, target_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON scholar_corrections TO glintstone;

COMMIT;
