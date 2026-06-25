-- Migration 060: scholar_claims + scholar_overrides — the Scholar Identity keystone (#17).
--
-- Two new tables bridge the two ends that already exist but were never connected:
--   * `users`    — live people who authenticated (uuid PK, orcid_id, role).
--   * `scholars` — 20,490 ORACC-ingested records (integer PK, orcid, institution).
-- There was no way for a logged-in user to say "that scholar record is me." These
-- tables add that link (scholar_claims) and a re-ingestion-safe place for the
-- claimant to edit their own bio (scholar_overrides).
--
-- PK-type bridge: user_id uuid ↔ scholar_id integer. The mismatch is deliberate
-- and load-bearing — scholar_claims is the only thing that joins the two.
--
-- DECISIONS BAKED IN (designer spec, Eric-approved defaults):
--   1. ORCID match auto-approves; manual claims always go to admin review.
--   2. One APPROVED claim per scholar (partial unique index) — a scholar is one
--      person. A user MAY claim multiple scholar rows (ORACC duplicate records).
--   3. Bio overlay fields = bio / institution / homepage_url / expertise_* only.
--   4. Public page shows the verified badge + bio ONLY after approval.
--
-- WHY scholar_overrides is a SEPARATE OVERLAY TABLE, not columns on `scholars`:
--   `scholars` is ORACC-ingested and RE-ingested. A `bio` column on it would be
--   clobbered on the next ingestion pass. The overlay is a table the ingestion
--   pipeline never writes, so user edits are structurally safe from re-ingestion
--   (the CLAUDE.md non-negotiable: never silently overwrite ingested data). The
--   read model does LEFT JOIN + COALESCE(override, ingested) per field.
--
-- GRANT: both tables are owned by wittkensis (migrations run as wittkensis); the
-- app connects as glintstone, so GRANT the CRUD set after creating each table.
--
-- Idempotent: CREATE TABLE IF NOT EXISTS + CREATE ... IF NOT EXISTS on every
-- index, so re-running the migration is a no-op.

BEGIN;

-- ── Part 1: scholar_claims — who claimed which scholar, how, and its status ──

CREATE TABLE IF NOT EXISTS scholar_claims (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             uuid    NOT NULL REFERENCES users(id)    ON DELETE CASCADE,
    scholar_id          integer NOT NULL REFERENCES scholars(id) ON DELETE CASCADE,
    status              text    NOT NULL DEFAULT 'pending'
                          CHECK (status IN ('pending', 'approved', 'rejected')),
    verification_method text    NOT NULL
                          CHECK (verification_method IN ('orcid_match', 'manual_review')),
    claim_note          text,                 -- optional user message ("I am the author of…")
    claimed_at          timestamptz NOT NULL DEFAULT now(),
    verified_at         timestamptz,          -- set on approve (or on insert for orcid_match)
    verified_by         uuid REFERENCES users(id),  -- admin who acted; NULL = system (orcid_match)
    review_note         text                  -- admin's reason on reject (shown to the user)
);

-- One APPROVED claim per scholar (decision #2): a scholar is one person. A second
-- user trying to claim an already-approved record is rejected with 409.
CREATE UNIQUE INDEX IF NOT EXISTS uq_scholar_claims_approved_scholar
    ON scholar_claims (scholar_id) WHERE status = 'approved';

-- A user can't file two PENDING claims on the same scholar (no duplicate queue spam).
-- A rejected row does NOT block a fresh attempt (re-claim after rejection is allowed).
CREATE UNIQUE INDEX IF NOT EXISTS uq_scholar_claims_pending_pair
    ON scholar_claims (user_id, scholar_id) WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_scholar_claims_user
    ON scholar_claims (user_id);
CREATE INDEX IF NOT EXISTS idx_scholar_claims_status_pending
    ON scholar_claims (status) WHERE status = 'pending';

GRANT SELECT, INSERT, UPDATE, DELETE ON scholar_claims TO glintstone;


-- ── Part 2: scholar_overrides — the bio overlay (sparse; one row per claim) ──

CREATE TABLE IF NOT EXISTS scholar_overrides (
    scholar_id          integer PRIMARY KEY REFERENCES scholars(id) ON DELETE CASCADE,
    edited_by_user_id   uuid    NOT NULL REFERENCES users(id),  -- the verified claimant
    bio                 text,                 -- ~1500 char (enforced in the API, not the DB)
    institution         text,                 -- overrides scholars.institution
    homepage_url        text,
    expertise_periods   text,                 -- overrides scholars.expertise_periods
    expertise_languages text,                 -- overrides scholars.expertise_languages
    updated_at          timestamptz NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON scholar_overrides TO glintstone;

COMMIT;
